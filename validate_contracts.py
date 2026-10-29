#!/usr/bin/env python3
"""ISTMOSAR JP-06 contract validator (research tooling, not part of any competition application).

Run from the repository root (Windows, macOS, Linux):

    pip install -r contracts/requirements.txt
    python validate_contracts.py              # offline: every stage below except --verify-catalog
    python validate_contracts.py -v           # also list every passing check
    python validate_contracts.py --verify-catalog   # ONLINE: compare VERIFIED_METADATA scenes with live NASA CMR

Stages
  1. Schemas      load every contracts/schemas/*.schema.json, check Draft 2020-12 validity, resolve every $ref locally.
  2. Fixtures     validate every file in contracts/examples/ against the schema named in contracts/fixtures-manifest.json.
  3. Business     cross-file rules BR-01..BR-15 that JSON Schema cannot express (references, units, time order, ...).
  4. Mutations    apply each declared mutation to a fixture and require the declared outcome (reject at schema stage,
                  reject at business stage, or stay valid).
  5. Manifest     every file in contracts/examples/ is registered, categories are consistent.

Exit status: 0 = all checks passed, 1 = at least one check failed, 2 = environment or file error.

IMPORTANT: a PASS proves the JSON is well-formed and internally consistent with the contract. It does NOT prove that any
NISAR observation, pair, raster or statistic is scientifically correct or approved.
"""
import argparse
import copy
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

try:
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    from referencing.exceptions import Unresolvable
    from referencing.jsonschema import DRAFT202012
except ImportError as exc:  # pragma: no cover
    print("ERROR: missing dependency (%s). Run: pip install -r contracts/requirements.txt" % exc)
    sys.exit(2)

ROOT = Path(__file__).resolve().parent
CONTRACTS = ROOT / "contracts"
SCHEMA_DIR = CONTRACTS / "schemas"
EXAMPLE_DIR = CONTRACTS / "examples"
MANIFEST = CONTRACTS / "fixtures-manifest.json"
BASE = "https://spacedogs.example/istmosar/contracts/v1/"
DRAFT_URI = "https://json-schema.org/draft/2020-12/schema"
CATEGORIES = {"VERIFIED_METADATA", "PROPOSED_STRUCTURE", "SIMULATED_DATA", "UNAVAILABLE", "PROCESSED_NISAR_DATA"}
CHECK_IDS = ["TEMPORAL_INDEPENDENCE", "SAME_TRACK", "SAME_DIRECTION", "SAME_FRAME", "SAME_RADAR_MODE",
             "COMPATIBLE_MATURITY_AND_VERSION", "CATALOG_FOOTPRINT_OVERLAP", "CHANNEL_VERIFIED_IN_BOTH",
             "SAME_MEASUREMENT_CONVENTION", "VALID_PIXEL_OVERLAP", "GRID_ALIGNMENT", "QUALITY_REVIEW"]
CATALOG_LEVEL, HDF5_LEVEL, PIXEL_LEVEL = CHECK_IDS[:7], CHECK_IDS[7:9], CHECK_IDS[9:11]
GRANULE_RE = re.compile(
    r"^NISAR_L2_(?P<pt>[A-Z]{2})_GCOV_(?P<cycle>\d{3})_(?P<track>\d{3})_(?P<dir>[AD])_(?P<frame>\d{3})_(?P<mode>\d{4})_"
    r"(?P<pole>[A-Z]{4})_(?P<src>[AM])_(?P<start>\d{8}T\d{6})_(?P<end>\d{8}T\d{6})_(?P<crid>[A-Z]\d{5})_(?P<acc>[PMNF])_"
    r"(?P<cov>[FP])_(?P<loc>[A-Z])_(?P<ctr>\d{3})$")
SECRET_KEY_RE = re.compile(r"(token|secret|passw(or)?d|credential|api[_-]?key|authorization|cookie)", re.I)
SECRET_VALUE_RES = [
    re.compile(r"[A-Za-z]:\\"), re.compile(r"\\\\[A-Za-z0-9_.-]+\\"), re.compile(r"file://", re.I),
    re.compile(r"(^|\s)/(home|Users|mnt|tmp|var)/"), re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\."),
    re.compile(r"bearer\s+[A-Za-z0-9._-]{10,}", re.I), re.compile(r"(passw(or)?d|secret|api[_-]?key|access[_-]?token)\s*[:=]", re.I)]
PANAMA_LON, PANAMA_LAT = (-83.5, -77.0), (7.0, 10.0)   # generous plausibility envelope; catches lat/lon swaps
N_RULES = 15


class Report:
    def __init__(self, verbose):
        self.verbose, self.failures, self.passes = verbose, [], 0

    def ok(self, msg):
        self.passes += 1
        if self.verbose:
            print("  pass  " + msg)

    def fail(self, msg):
        self.failures.append(msg)
        print("  FAIL  " + msg)


# ----------------------------------------------------------------------------- loading helpers
def _no_dupes(pairs):
    seen = {}
    for k, v in pairs:
        if k in seen:
            raise ValueError("duplicate JSON key %r" % k)
        seen[k] = v
    return seen


def load_json(path):
    raw = Path(path).read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        print("  warn  %s starts with a UTF-8 BOM; save it without BOM for portability" % Path(path).name)
    return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_no_dupes)   # utf-8-sig tolerates Windows BOMs


def parse_ts(s):
    m = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,6}))?Z$", s)
    if not m:
        raise ValueError("bad timestamp %r" % s)
    frac = (m.group(2) or "0").ljust(6, "0")
    return datetime.strptime(m.group(1) + "." + frac, "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)


def collect_refs(node, out):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "$ref" and isinstance(v, str):
                out.append(v)
            else:
                collect_refs(v, out)
    elif isinstance(node, list):
        for v in node:
            collect_refs(v, out)


# ----------------------------------------------------------------------------- stage 1: schemas
def stage_schemas(rep):
    print("[1/5] Schemas")
    paths = sorted(SCHEMA_DIR.glob("*.schema.json"))
    if not paths:
        rep.fail("no schemas found in %s" % SCHEMA_DIR)
        return None, None
    schemas, registry, ids = {}, Registry(), {}
    for p in paths:
        try:
            s = load_json(p)
        except Exception as exc:
            rep.fail("%s: cannot parse (%s)" % (p.name, exc))
            continue
        schemas[p.name] = s
        if s.get("$schema") != DRAFT_URI:
            rep.fail("%s: $schema must be %s" % (p.name, DRAFT_URI))
        sid = s.get("$id")
        if sid != BASE + p.name:
            rep.fail("%s: $id must be %s (found %r)" % (p.name, BASE + p.name, sid))
        elif sid in ids:
            rep.fail("%s: duplicate $id" % p.name)
        else:
            ids[sid] = p.name
            registry = registry.with_resource(sid, Resource.from_contents(s, default_specification=DRAFT202012))
        try:
            Draft202012Validator.check_schema(s)
            rep.ok("%s is a valid Draft 2020-12 schema" % p.name)
        except Exception as exc:
            rep.fail("%s: invalid schema (%s)" % (p.name, str(exc).splitlines()[0]))
    n_refs, graph = 0, {}
    for name, s in schemas.items():
        refs = []
        collect_refs(s, refs)
        sid = s.get("$id", BASE + name)
        resolver = registry.resolver(base_uri=sid)
        graph[name] = set()
        for r in refs:
            n_refs += 1
            full = urljoin(sid, r)
            if not full.startswith(BASE):
                rep.fail("%s: $ref %r leaves the contract namespace (no remote references allowed)" % (name, r))
                continue
            target = full.split("#")[0][len(BASE):]
            if target != name:
                graph[name].add(target)
            try:
                resolver.lookup(r)
            except Unresolvable:
                rep.fail("%s: unresolvable $ref %r" % (name, r))
            except Exception as exc:
                rep.fail("%s: cannot resolve $ref %r (%s)" % (name, r, exc))
    state = {}

    def visit(n, trail):
        if state.get(n) == 1:
            rep.fail("circular schema reference: " + " -> ".join(trail + [n]))
            return
        if state.get(n) == 2:
            return
        state[n] = 1
        for m in sorted(graph.get(n, ())):
            visit(m, trail + [n])
        state[n] = 2
    for n in graph:
        visit(n, [])
    rep.ok("%d schemas loaded, %d $ref occurrences resolved locally, no cycles" % (len(schemas), n_refs))
    missing = [f for f in ("date-time", "uri", "date") if f not in Draft202012Validator.FORMAT_CHECKER.checkers]
    if missing:
        rep.fail("format checkers missing for %s: format keywords would be silently ignored. "
                 "Run: pip install -r contracts/requirements.txt" % ", ".join(missing))
    else:
        rep.ok("format checkers active: date-time, uri, date")
    return schemas, registry


def make_validator(registry, schema_ref):
    return Draft202012Validator({"$schema": DRAFT_URI, "$ref": BASE + schema_ref}, registry=registry,
                                format_checker=Draft202012Validator.FORMAT_CHECKER)


def _flatten(err, depth=0):
    """Yield (path, message) for an error and, for anyOf/oneOf, for the sub-errors that explain it."""
    yield "/".join(str(p) for p in err.absolute_path) or "(root)", err.message[:200]
    if depth < 3:
        for sub in err.context or ():
            yield from _flatten(sub, depth + 1)


def schema_errors(validator, instance):
    errs = sorted(validator.iter_errors(instance), key=lambda e: [str(p) for p in e.absolute_path])
    out = []
    for e in errs:
        parts = list(_flatten(e))
        head = "%s: %s" % parts[0]
        if len(parts) > 1:
            head += " [" + "; ".join("%s: %s" % x for x in parts[1:7]) + "]"
        out.append(head)
    return out


# ----------------------------------------------------------------------------- JSON-pointer patch (add / replace / remove)
def _unesc(tok):
    return tok.replace("~1", "/").replace("~0", "~")


def apply_patch(doc, patch):
    doc = copy.deepcopy(doc)
    for op in patch:
        toks = [_unesc(t) for t in op["path"].split("/")[1:]]
        parent = doc
        for t in toks[:-1]:
            parent = parent[int(t)] if isinstance(parent, list) else parent[t]
        last = toks[-1]
        if isinstance(parent, list):
            idx = len(parent) if last == "-" else int(last)
            if op["op"] == "add":
                parent.insert(idx, copy.deepcopy(op["value"]))
            elif op["op"] == "replace":
                parent[idx] = copy.deepcopy(op["value"])
            elif op["op"] == "remove":
                del parent[idx]
        else:
            if op["op"] in ("add", "replace"):
                if op["op"] == "replace" and last not in parent:
                    raise KeyError("replace target missing: " + op["path"])
                parent[last] = copy.deepcopy(op["value"])
            elif op["op"] == "remove":
                del parent[last]
            else:
                raise ValueError("unsupported op " + op["op"])
    return doc


# ----------------------------------------------------------------------------- stage 3: business rules
def walk_strings(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk_strings(v, path + "/" + str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_strings(v, "%s/%d" % (path, i))
    elif isinstance(node, str):
        yield path, node


def walk_keys(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield path + "/" + str(k), str(k)
            yield from walk_keys(v, path + "/" + str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_keys(v, "%s/%d" % (path, i))


def bbox_ok(b):
    return b[0] < b[2] and b[1] < b[3]


def bbox_inside(inner, outer, tol=1e-9):
    return inner[0] >= outer[0] - tol and inner[1] >= outer[1] - tol and inner[2] <= outer[2] + tol and inner[3] <= outer[3] + tol


def ring_bbox(poly):
    xs = [p[0] for p in poly["coordinates"][0]]
    ys = [p[1] for p in poly["coordinates"][0]]
    return [min(xs), min(ys), max(xs), max(ys)]


def ring_area(ring):
    return abs(sum(ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1] for i in range(len(ring) - 1))) / 2.0


def business_rules(world):
    """world: {filename: (kind, obj, category)}. Returns a list of 'BR-xx file: message' strings."""
    v = []
    areas = {o["id"]: (f, o) for f, (k, o, c) in world.items() if k == "study-area"}
    scenes = {o["id"]: (f, o) for f, (k, o, c) in world.items() if k == "scene"}
    analyses = {o["id"]: (f, o) for f, (k, o, c) in world.items() if k == "analysis"}
    layers = {o["id"]: (f, o) for f, (k, o, c) in world.items() if k == "layer"}
    sim = lambda o: o.get("data_category") == "SIMULATED_DATA"

    # BR-11 / BR-13 apply to every fixture
    for f, (k, o, c) in world.items():
        for p, key in walk_keys(o):
            if SECRET_KEY_RE.search(key):
                v.append("BR-11 %s: credential-like key at %s" % (f, p))
        for p, s in walk_strings(o):
            if any(r.search(s) for r in SECRET_VALUE_RES):
                v.append("BR-11 %s: local path or credential-like text at %s" % (f, p))
            if s.startswith("https://"):
                is_fake = s.split("/")[2] == "example.invalid"
                if c == "SIMULATED_DATA" and not is_fake:
                    v.append("BR-13 %s: simulated record uses a non-example.invalid URL at %s" % (f, p))
                if c != "SIMULATED_DATA" and is_fake and k not in ("api", "error"):
                    v.append("BR-13 %s: non-simulated record uses example.invalid at %s" % (f, p))
        if c == "SIMULATED_DATA" and ".simulated." not in f:
            v.append("BR-13 %s: SIMULATED_DATA fixture file name must contain '.simulated.'" % f)
        if ".simulated." in f and c != "SIMULATED_DATA":
            v.append("BR-13 %s: '.simulated.' file is not categorised SIMULATED_DATA" % f)

    # BR-04 geometry (study areas)
    for f, a in areas.values():
        b = a["bbox_lonlat"]
        if not bbox_ok(b):
            v.append("BR-04 %s: bbox_lonlat must satisfy west < east and south < north, got %s" % (f, b))
        elif a["country"] == "PA" and not (PANAMA_LON[0] <= b[0] and b[2] <= PANAMA_LON[1] and PANAMA_LAT[0] <= b[1] and b[3] <= PANAMA_LAT[1]):
            v.append("BR-04 %s: bbox %s is outside the Panama plausibility envelope lon %s lat %s (swapped latitude/longitude?)" % (f, b, PANAMA_LON, PANAMA_LAT))
        g = a.get("geometry")
        if g:
            r = g["coordinates"][0]
            if r[0] != r[-1]:
                v.append("BR-04 %s: polygon ring is not closed" % f)
            if bbox_ok(b) and not bbox_inside(ring_bbox(g), b):
                v.append("BR-04 %s: geometry extends outside bbox_lonlat" % f)

    # scenes
    for f, s in scenes.values():
        t0, t1 = parse_ts(s["acquisition_start_utc"]), parse_ts(s["acquisition_end_utc"])
        if t1 < t0:
            v.append("BR-05 %s: acquisition_end_utc precedes acquisition_start_utc" % f)
        fp = s.get("footprint")
        if fp:
            r = fp["coordinates"][0]
            if r[0] != r[-1]:
                v.append("BR-04 %s: footprint ring is not closed" % f)
            elif ring_area(r) == 0:
                v.append("BR-04 %s: footprint has zero area" % f)
        if not sim(s):
            m = GRANULE_RE.match(s["granule_id"])
            if not m:
                v.append("BR-03 %s: granule_id does not follow the NISAR naming convention" % f)
            else:
                g = m.groupdict()
                chk = [("cycle", int(g["cycle"]), s["cycle"]), ("track", int(g["track"]), s["track"]), ("frame", int(g["frame"]), s["frame"]),
                       ("direction", {"A": "ASCENDING", "D": "DESCENDING"}[g["dir"]], s["direction"]), ("radar_mode_code", g["mode"], s["radar_mode_code"]),
                       ("acquisition_start_utc", g["start"], re.sub(r"[-:]", "", s["acquisition_start_utc"][:19])),
                       ("acquisition_end_utc", g["end"], re.sub(r"[-:]", "", s["acquisition_end_utc"][:19])), ("crid", g["crid"], s["crid"])]
                if s.get("frame_coverage"):
                    chk.append(("frame_coverage", {"F": "FULL", "P": "PARTIAL"}[g["cov"]], s["frame_coverage"]))
                for name, from_id, field in chk:
                    if from_id != field:
                        v.append("BR-03 %s: %s is %r but granule_id says %r" % (f, name, field, from_id))
            if s["cmr_concept_id"] and s["cmr_concept_id"] not in s["source_url"]:
                v.append("BR-03 %s: source_url does not contain cmr_concept_id" % f)
            if s.get("file") and s["file"]["name"] != s["granule_id"] + ".h5":
                v.append("BR-03 %s: file.name is not granule_id + .h5" % f)
            for key in ("PROVISIONAL", "BETA", "VALIDATED"):
                if key in s["collection"] and s["product_maturity"] != key:
                    v.append("BR-03 %s: collection says %s but product_maturity is %s" % (f, key, s["product_maturity"]))
        lid = s.get("raster_layer_id")
        if lid:
            if lid not in layers:
                v.append("BR-01 %s: raster_layer_id %r does not exist" % (f, lid))
            elif layers[lid][1]["parent"] != {"type": "SCENE", "id": s["id"]}:
                v.append("BR-01 %s: raster layer %r is not a child of this scene" % (f, lid))
        if s.get("extraction_status") != "EXTRACTED" and any(
                l["parent"] == {"type": "SCENE", "id": s["id"]} and l["availability"] == "AVAILABLE" for _, l in layers.values()):
            v.append("BR-12 %s: an AVAILABLE layer exists but extraction_status is not EXTRACTED" % f)

    # layers
    for f, l in layers.values():
        par = l["parent"]
        if par["type"] == "ANALYSIS":
            if par["id"] not in analyses:
                v.append("BR-01 %s: parent analysis %r does not exist" % (f, par["id"]))
            else:
                pa = analyses[par["id"]][1]
                if l["id"] not in pa["layer_ids"]:
                    v.append("BR-01 %s: layer is not listed in analysis.layer_ids" % f)
                if pa["compatibility"]["decision"] != "GO":
                    v.append("BR-12 %s: layers may only belong to a GO analysis" % f)
                if l["quality_status"] == "PASSED" and pa["lifecycle_status"] != "COMPLETED":
                    v.append("BR-12 %s: quality PASSED but analysis is not COMPLETED" % f)
                if l["provenance_id"] != pa["provenance"]["id"]:
                    v.append("BR-01 %s: provenance_id %r does not match the analysis provenance %r" % (f, l["provenance_id"], pa["provenance"]["id"]))
                if sim(l) != sim(pa) and l["data_category"] != "UNAVAILABLE":
                    v.append("BR-02 %s: layer and analysis disagree on SIMULATED_DATA" % f)
                if pa["area_id"] in areas and l.get("raster"):
                    ab = areas[pa["area_id"]][1]["bbox_lonlat"]
                    if not bbox_inside(l["raster"]["bounds_lonlat"], ab):
                        v.append("BR-04 %s: raster bounds %s lie outside study area %s" % (f, l["raster"]["bounds_lonlat"], ab))
                if not set(l["source_scene_ids"]) <= set(pa["scene_ids"]):
                    v.append("BR-01 %s: source_scene_ids are not part of the analysis pair" % f)
        elif par["id"] not in scenes:
            v.append("BR-01 %s: parent scene %r does not exist" % (f, par["id"]))
        for sid in l["source_scene_ids"]:
            if sid not in scenes:
                v.append("BR-01 %s: source scene %r does not exist" % (f, sid))
            elif sim(scenes[sid][1]) != sim(l) and l["data_category"] != "UNAVAILABLE":
                v.append("BR-02 %s: layer and source scene %r disagree on SIMULATED_DATA" % (f, sid))
        r = l.get("raster")
        if r:
            if not bbox_ok(r["bounds_lonlat"]):
                v.append("BR-04 %s: raster bounds must satisfy west < east and south < north" % f)
            if l["delivery"]["method"] == "IMAGE_OVERLAY" and l["delivery"]["image_bounds_lonlat"] != r["bounds_lonlat"]:
                v.append("BR-04 %s: overlay image bounds differ from raster bounds" % f)
        db = l["delivery"].get("image_bounds_lonlat")
        if db and not bbox_ok(db):
            v.append("BR-04 %s: overlay bounds must satisfy west < east and south < north" % f)

    # analyses
    for f, a in analyses.values():
        if a["area_id"] not in areas:
            v.append("BR-01 %s: area_id %r does not exist" % (f, a["area_id"]))
        elif sim(areas[a["area_id"]][1]) != sim(a):
            v.append("BR-02 %s: analysis and study area disagree on SIMULATED_DATA" % f)
        pair, missing = [], False
        for sid in a["scene_ids"]:
            if sid not in scenes:
                v.append("BR-01 %s: scene %r does not exist" % (f, sid))
                missing = True
            else:
                pair.append(scenes[sid][1])
                if sim(scenes[sid][1]) != sim(a):
                    v.append("BR-02 %s: analysis and scene %r disagree on SIMULATED_DATA (real and simulated records must never mix)" % (f, sid))
        for lid in a["layer_ids"]:
            if lid not in layers:
                v.append("BR-01 %s: layer %r does not exist" % (f, lid))
            elif layers[lid][1]["parent"] != {"type": "ANALYSIS", "id": a["id"]}:
                v.append("BR-01 %s: layer %r does not name this analysis as parent" % (f, lid))
        st = a["statistics"]
        if a["data_category"] == "SIMULATED_DATA" and st["data_category"] not in ("SIMULATED_DATA", "UNAVAILABLE"):
            v.append("BR-02 %s: statistics category %s inside a simulated analysis" % (f, st["data_category"]))
        if a["data_category"] != "SIMULATED_DATA" and st["data_category"] == "SIMULATED_DATA":
            v.append("BR-02 %s: simulated statistics inside a non-simulated analysis" % f)
        comp = a["compatibility"]
        ids = [c["check_id"] for c in comp["checks"]]
        res = {c["check_id"]: c["result"] for c in comp["checks"]}
        if sorted(ids) != sorted(CHECK_IDS):
            v.append("BR-06 %s: compatibility.checks must contain each of the %d check ids exactly once" % (f, len(CHECK_IDS)))
        else:
            if comp["decision"] == "GO" and any(res[c] != "PASS" for c in CATALOG_LEVEL):
                v.append("BR-06 %s: GO requires every catalog-level check to PASS" % f)
            if comp["decision"] == "INSUFFICIENT_EVIDENCE" and all(res[c] != "NOT_EVALUATED" for c in CATALOG_LEVEL):
                v.append("BR-06 %s: INSUFFICIENT_EVIDENCE needs a catalog-level check that is NOT_EVALUATED (otherwise the decision is GO)" % f)
            lvl = comp["evidence_level"]
            if lvl in ("HDF5_METADATA", "PIXEL_CHECKS_PASSED") and any(res[c] != "PASS" for c in HDF5_LEVEL):
                v.append("BR-06 %s: evidence_level %s requires the HDF5-level checks to PASS" % (f, lvl))
            if lvl == "PIXEL_CHECKS_PASSED" and any(res[c] != "PASS" for c in PIXEL_LEVEL):
                v.append("BR-06 %s: PIXEL_CHECKS_PASSED requires VALID_PIXEL_OVERLAP and GRID_ALIGNMENT to PASS" % f)
            if a["approval"]["status"] == "APPROVED" and comp["decision"] == "GO" and res["QUALITY_REVIEW"] != "PASS":
                v.append("BR-06 %s: an APPROVED GO analysis requires QUALITY_REVIEW = PASS" % f)
        if missing or len(pair) != 2:
            continue
        s1, s2 = pair
        same_pass = s1["cycle"] == s2["cycle"] and s1["track"] == s2["track"]
        t1, t2 = parse_ts(s1["acquisition_start_utc"]), parse_ts(s2["acquisition_start_utc"])
        tr = a["temporal_relationship"]
        if same_pass and tr["classification"] != "SAME_ACQUISITION":
            v.append("BR-05 %s: both scenes share cycle %d and track %d (one pass) so classification must be SAME_ACQUISITION" % (f, s1["cycle"], s1["track"]))
        if not same_pass and tr["classification"] == "SAME_ACQUISITION":
            v.append("BR-05 %s: SAME_ACQUISITION declared but the scenes have different cycle/track" % f)
        if same_pass and res.get("TEMPORAL_INDEPENDENCE") == "PASS":
            v.append("BR-05 %s: TEMPORAL_INDEPENDENCE cannot PASS for two scenes of the same pass" % f)
        if not same_pass and res.get("TEMPORAL_INDEPENDENCE") == "FAIL":
            v.append("BR-05 %s: TEMPORAL_INDEPENDENCE is FAIL but the scenes come from different cycles/tracks" % f)
        if tr["interval_seconds"] is not None and abs(abs((t2 - t1).total_seconds()) - tr["interval_seconds"]) > 1:
            v.append("BR-05 %s: interval_seconds %s does not match the acquisition start times" % (f, tr["interval_seconds"]))
        if tr["classification"] == "DISTINCT_ACQUISITIONS" and tr["earlier_scene_id"] and tr["later_scene_id"]:
            early, late = (s1, s2) if t1 <= t2 else (s2, s1)
            if tr["earlier_scene_id"] != early["id"] or tr["later_scene_id"] != late["id"]:
                v.append("BR-05 %s: earlier/later scene ids contradict the acquisition times (Delta_dB sign would invert)" % f)
        objective = {"SAME_TRACK": s1["track"] == s2["track"], "SAME_DIRECTION": s1["direction"] == s2["direction"], "SAME_FRAME": s1["frame"] == s2["frame"],
                     "SAME_RADAR_MODE": s1["radar_mode_code"] == s2["radar_mode_code"],
                     "COMPATIBLE_MATURITY_AND_VERSION": s1["product_maturity"] == s2["product_maturity"] and
                     (s1["product_version"] == s2["product_version"] or None in (s1["product_version"], s2["product_version"]))}
        for cid, truth in objective.items():
            if res.get(cid) == "PASS" and not truth:
                v.append("BR-06 %s: %s is PASS but the scene metadata disagree" % (f, cid))
            if res.get(cid) == "FAIL" and truth:
                v.append("BR-06 %s: %s is FAIL but the scene metadata agree" % (f, cid))
        if res.get("CATALOG_FOOTPRINT_OVERLAP") == "PASS":
            if not (s1["footprint"] and s2["footprint"]):
                v.append("BR-06 %s: CATALOG_FOOTPRINT_OVERLAP is PASS but a footprint is missing" % f)
            else:
                b1, b2 = ring_bbox(s1["footprint"]), ring_bbox(s2["footprint"])
                if b1[0] >= b2[2] or b2[0] >= b1[2] or b1[1] >= b2[3] or b2[1] >= b1[3]:
                    v.append("BR-06 %s: CATALOG_FOOTPRINT_OVERLAP is PASS but the footprints do not overlap" % f)
        sc = a["selected_channel"]
        lvl = comp["evidence_level"]
        if lvl in ("HDF5_METADATA", "PIXEL_CHECKS_PASSED") and any(s["hdf5_inspection"]["status"] != "INSPECTED" for s in pair):
            v.append("BR-07 %s: evidence_level %s but a scene HDF5 file was never inspected" % (f, lvl))
        if sc:
            for s in pair:
                fr = [x for x in s["frequencies"] if x["band"] == sc["frequency_band"]]
                if not fr:
                    v.append("BR-07 %s: scene %s has no frequency %s" % (f, s["id"], sc["frequency_band"]))
                    continue
                if sc["covariance_term"][:2] not in fr[0]["polarizations_nominal"]:
                    v.append("BR-07 %s: %s needs polarization %s, not nominal in scene %s" % (f, sc["covariance_term"], sc["covariance_term"][:2], s["id"]))
                if (a["lifecycle_status"] in ("PROCESSING", "COMPLETED") or lvl in ("HDF5_METADATA", "PIXEL_CHECKS_PASSED")) and \
                        sc["covariance_term"] not in fr[0]["covariance_terms_verified"]:
                    v.append("BR-07 %s: channel %s was never verified in the HDF5 of scene %s" % (f, sc["covariance_term"], s["id"]))
        mine = [layers[i][1] for i in a["layer_ids"] if i in layers]
        sci = [l for l in mine if l["role"] in ("BEFORE", "AFTER", "CHANGE")]
        for l in sci:
            m = l["measurement"]
            if a["measurement_convention"] and m["convention"] != a["measurement_convention"]:
                v.append("BR-09 %s: layer %s uses %s but the analysis declares %s (gamma0 and sigma0 must not be mixed)" % (f, l["id"], m["convention"], a["measurement_convention"]))
            if sc and (m["covariance_term"], m["frequency_band"]) != (sc["covariance_term"], sc["frequency_band"]):
                v.append("BR-09 %s: layer %s channel differs from selected_channel" % (f, l["id"]))
            role_scene = {"BEFORE": tr["earlier_scene_id"], "AFTER": tr["later_scene_id"]}.get(l["role"])
            if l["role"] in ("BEFORE", "AFTER") and role_scene and l["source_scene_ids"] != [role_scene]:
                v.append("BR-09 %s: %s layer %s is not built from the %s scene" % (f, l["role"], l["id"], "earlier" if l["role"] == "BEFORE" else "later"))
            if l["role"] == "CHANGE" and set(l["source_scene_ids"]) != set(a["scene_ids"]):
                v.append("BR-09 %s: CHANGE layer %s must cite both scenes" % (f, l["id"]))
        pv = a["provenance"]
        if {s["scene_id"] for s in pv["sources"]} != set(a["scene_ids"]):
            v.append("BR-10 %s: provenance.sources do not match scene_ids" % f)
        for src in pv["sources"]:
            if src["scene_id"] in scenes:
                sc_ = scenes[src["scene_id"]][1]
                if src["granule_id"] != sc_["granule_id"] or src["cmr_concept_id"] != sc_["cmr_concept_id"]:
                    v.append("BR-10 %s: provenance source %s disagrees with the scene record" % (f, src["scene_id"]))
                if sc_.get("file") and src["catalog_checksum"] != sc_["file"]["catalog_checksum"]:
                    v.append("BR-10 %s: provenance catalog checksum for %s differs from the scene record" % (f, src["scene_id"]))
        pr = pv.get("processing")
        if pr:
            if a["measurement_convention"] != pr["measurement_convention"]:
                v.append("BR-09 %s: analysis and provenance disagree on measurement convention" % f)
            if sc != pr["selected_channel"]:
                v.append("BR-09 %s: analysis and provenance disagree on selected channel" % f)
            if pr["parameters"] != a["parameters"]:
                v.append("BR-09 %s: provenance parameters differ from analysis parameters" % f)
            art = {o["artifact_id"] for o in pv["outputs"]}
            for l in mine:
                if l.get("raster"):
                    if l["raster"]["artifact_id"] not in art:
                        v.append("BR-10 %s: layer %s artifact %s is missing from provenance.outputs" % (f, l["id"], l["raster"]["artifact_id"]))
                    if l["raster"]["crs"] != pr["destination_crs"]:
                        v.append("BR-10 %s: layer %s CRS differs from provenance destination_crs" % (f, l["id"]))
        # BR-08 statistics arithmetic and units
        if st["data_category"] != "UNAVAILABLE":
            tot, val, inv, chg = st["total_pixels_inspected"], st["valid_pixel_count"], st["invalid_pixel_count"], st["changed_pixel_count"]
            if tot != val + inv:
                v.append("BR-08 %s: total_pixels_inspected (%s) != valid (%s) + invalid (%s)" % (f, tot, val, inv))
            if chg > val:
                v.append("BR-08 %s: changed_pixel_count exceeds valid_pixel_count" % f)
            if val > 0:
                if st["changed_pixel_pct"] is None or abs(st["changed_pixel_pct"] - 100.0 * chg / val) > 0.01:
                    v.append("BR-08 %s: changed_pixel_pct %s is not 100*changed/valid = %.4f" % (f, st["changed_pixel_pct"], 100.0 * chg / val))
            elif st["changed_pixel_pct"] is not None or st["mean_delta_db"] is not None:
                v.append("BR-08 %s: with zero valid pixels the percentage and mean must be null" % f)
            if st["change_threshold"] and a["parameters"]["change_threshold_db"] != st["change_threshold"]["value"]:
                v.append("BR-08 %s: statistics threshold differs from parameters.change_threshold_db" % f)
            chl = [l for l in sci if l["role"] == "CHANGE" and l.get("raster")]
            if chl:
                g = chl[0]["raster"]["grid"]
                if tot != g["width_px"] * g["height_px"]:
                    v.append("BR-08 %s: total_pixels_inspected != change-layer width*height" % f)
                if st["area_method"] in ("EQUAL_AREA_GRID", "UTM_PLANIMETRIC_APPROX") and g["pixel_size_unit"] != "m":
                    v.append("BR-08 %s: area cannot be derived from %s pixel spacing (degrees are not metres)" % (f, g["pixel_size_unit"]))
                elif st["area_method"] == "EQUAL_AREA_GRID" and st["changed_area_km2"] is not None:
                    exp = chg * g["pixel_size_x"] * g["pixel_size_y"] / 1e6
                    if abs(exp - st["changed_area_km2"]) > max(0.01 * exp, 0.001):
                        v.append("BR-08 %s: changed_area_km2 %s != changed pixels x pixel area = %.4f km2" % (f, st["changed_area_km2"], exp))
                    if st["area_crs"] != chl[0]["raster"]["crs"]:
                        v.append("BR-08 %s: area_crs differs from the change-layer CRS" % f)
            if st["area_method"] == "NOT_CALCULATED" and st["changed_area_km2"] is not None:
                v.append("BR-08 %s: changed_area_km2 given but area_method is NOT_CALCULATED" % f)
    # BR-14 analyses that are not GO own no layers
    for f, l in layers.values():
        if l["parent"]["type"] == "ANALYSIS" and l["parent"]["id"] in analyses and analyses[l["parent"]["id"]][1]["compatibility"]["decision"] != "GO":
            v.append("BR-14 %s: layer exists for an analysis that is not GO" % f)
    # BR-15 embedded copies must equal the canonical fixture (drift detection)
    for f, (k, o, c) in world.items():
        if k == "api" and isinstance(o, dict) and isinstance(o.get("items"), list):
            for it in o["items"]:
                for reg in (areas, scenes, analyses, layers):
                    if it.get("id") in reg and reg[it["id"]][1] != it:
                        v.append("BR-15 %s: embedded item %s differs from its fixture %s" % (f, it["id"], reg[it["id"]][0]))
    return v


# ----------------------------------------------------------------------------- optional online check
def compare_scene_with_umm(scene, umm):
    """Compare one VERIFIED_METADATA scene with an official CMR UMM-G record (dict). Returns a list of mismatches."""
    bad = []
    dg = umm.get("DataGranule", {})
    pid = [i["Identifier"] for i in dg.get("Identifiers", []) if i.get("IdentifierType") == "ProducerGranuleId"]
    if pid != [scene["granule_id"]]:
        bad.append("granule_id: fixture %r vs CMR %r" % (scene["granule_id"], pid))
    rng = umm.get("TemporalExtent", {}).get("RangeDateTime", {})
    for key, field in (("BeginningDateTime", "acquisition_start_utc"), ("EndingDateTime", "acquisition_end_utc")):
        try:
            if abs((parse_ts(scene[field]) - parse_ts(rng[key])).total_seconds()) > 0.001:
                bad.append("%s: fixture %s vs CMR %s" % (field, scene[field], rng[key]))
        except (KeyError, ValueError):
            bad.append("%s: cannot compare with CMR %s" % (field, rng.get(key)))
    h5 = [x for x in dg.get("ArchiveAndDistributionInformation", []) if x.get("Name") == scene["granule_id"] + ".h5"]
    if not h5:
        bad.append("CMR lists no %s.h5 file" % scene["granule_id"])
    elif scene.get("file"):
        if h5[0].get("SizeInBytes") != scene["file"]["size_bytes"]:
            bad.append("file.size_bytes: fixture %s vs CMR %s" % (scene["file"]["size_bytes"], h5[0].get("SizeInBytes")))
        cs = h5[0].get("Checksum", {})
        decl = scene["file"].get("catalog_checksum") or {}
        if cs.get("Value") != decl.get("value"):
            bad.append("file.catalog_checksum: fixture %s vs CMR %s %s" % (decl.get("value"), cs.get("Algorithm"), cs.get("Value")))
    pts = []
    for gp in umm.get("SpatialExtent", {}).get("HorizontalSpatialDomain", {}).get("Geometry", {}).get("GPolygons", []):
        pts = [[p["Longitude"], p["Latitude"]] for p in gp["Boundary"]["Points"]]
    fp = (scene.get("footprint") or {}).get("coordinates", [[]])[0]
    if len(pts) != len(fp) or any(abs(a[0] - b[0]) > 1e-6 or abs(a[1] - b[1]) > 1e-6 for a, b in zip(pts, fp)):
        bad.append("footprint differs from the CMR polygon (CMR stores latitude first)")
    attrs = {a["Name"]: a["Values"] for a in umm.get("AdditionalAttributes", [])}
    want = {"ASCENDING_DESCENDING": [scene["direction"]], "FRAME_NUMBER": [str(scene["frame"])], "TRACK_NUMBER": [str(scene["track"])]}
    if scene.get("product_version"):
        want["PRODUCT_VERSION"] = [scene["product_version"]]
    for k, val in want.items():
        if attrs.get(k) != val:
            bad.append("%s: fixture %s vs CMR %s" % (k, val, attrs.get(k)))
    if scene.get("frame_coverage") and attrs.get("FULL_FRAME") != [("TRUE" if scene["frame_coverage"] == "FULL" else "FALSE")]:
        bad.append("frame_coverage disagrees with CMR FULL_FRAME %s" % attrs.get("FULL_FRAME"))
    orb = [o.get("OrbitNumber") for o in umm.get("OrbitCalculatedSpatialDomains", [])]
    if scene.get("orbit_number") and orb != [scene["orbit_number"]]:
        bad.append("orbit_number: fixture %s vs CMR %s" % (scene["orbit_number"], orb))
    upd = [d.get("Date") for d in umm.get("ProviderDates", []) if d.get("Type") == "Update"]
    if scene.get("catalog_updated_utc") and upd:
        try:
            if abs((parse_ts(scene["catalog_updated_utc"]) - parse_ts(upd[-1])).total_seconds()) > 0.001:
                bad.append("catalog_updated_utc: fixture %s vs CMR %s (the catalog record changed after it was verified; re-verify)" % (scene["catalog_updated_utc"], upd[-1]))
        except ValueError:
            bad.append("catalog_updated_utc: cannot compare with CMR %s" % upd[-1])
    listed = {u.get("URL") for u in umm.get("RelatedUrls", [])}
    for url in scene.get("official_qa_references", []):
        if url not in listed:
            bad.append("official_qa_references: %s is not listed in the CMR RelatedUrls" % url)
    return bad


def stage_online(rep, world):
    print("[online] Comparing VERIFIED_METADATA scenes with live NASA CMR records")
    import urllib.request
    hard_error = False
    for f, (k, o, c) in sorted(world.items()):
        if k != "scene" or c != "VERIFIED_METADATA":
            continue
        try:
            req = urllib.request.Request(o["source_url"], headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                umm = json.loads(r.read().decode("utf-8-sig"))
        except Exception as exc:
            print("  ERROR %s: could not fetch %s (%s)" % (f, o["source_url"], exc))
            hard_error = True
            continue
        problems = compare_scene_with_umm(o, umm)
        for p in problems:
            rep.fail("%s differs from the official CMR record: %s" % (f, p))
        if not problems:
            rep.ok("%s matches the official CMR record" % f)
    return hard_error


# ----------------------------------------------------------------------------- main
KIND_BY_SCHEMA = {"study-area.schema.json": "study-area", "scene.schema.json": "scene", "analysis.schema.json": "analysis",
                  "layer.schema.json": "layer", "error.schema.json": "error"}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate the ISTMOSAR JP-06 data contract.")
    ap.add_argument("-v", "--verbose", action="store_true", help="list every passing check")
    ap.add_argument("--verify-catalog", action="store_true", help="ONLINE: compare VERIFIED_METADATA scenes with live NASA CMR records")
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    rep = Report(args.verbose)
    schemas, registry = stage_schemas(rep)
    if schemas is None or any(("unresolvable" in x) or ("invalid schema" in x) or ("cannot parse" in x) for x in rep.failures):
        print("\nRESULT: FAIL - schemas are not usable; later stages skipped.")
        return 1
    print("[2/5] Fixtures")
    try:
        manifest = load_json(MANIFEST)
    except Exception as exc:
        print("ERROR: cannot read %s (%s)" % (MANIFEST, exc))
        return 2
    world, validators, schema_of = {}, {}, {}
    for fx in manifest["fixtures"]:
        name, sref = fx["file"], fx["schema"]
        schema_of[name] = sref
        try:
            obj = load_json(EXAMPLE_DIR / name)
        except Exception as exc:
            rep.fail("%s: cannot load (%s)" % (name, exc))
            continue
        if sref.split("#")[0] not in schemas:
            rep.fail("%s: manifest names unknown schema %s" % (name, sref))
            continue
        validators.setdefault(sref, make_validator(registry, sref))
        errs = schema_errors(validators[sref], obj)
        for e in errs[:6]:
            rep.fail("%s: %s" % (name, e))
        if not errs:
            rep.ok("%s validates against %s (%s)" % (name, sref, fx["category"]))
        world[name] = (KIND_BY_SCHEMA.get(sref, "api"), obj, fx["category"])
    print("[3/5] Business rules BR-01..BR-%d over %d fixtures" % (N_RULES, len(world)))
    viol = business_rules(world)
    for x in viol:
        rep.fail(x)
    if not viol:
        rep.ok("no business-rule violations")
    cases = manifest.get("mutation_cases", [])
    print("[4/5] Mutation cases (%d)" % len(cases))
    counts = {"schema": 0, "business": 0, "valid": 0}
    for mc in cases:
        base = mc["base"]
        label = "%s %s" % (mc["id"], mc["title"])
        if base not in world:
            rep.fail("%s: base fixture %s is not registered or failed to load" % (mc["id"], base))
            continue
        kind, obj, cat = world[base]
        try:
            mutated = apply_patch(obj, mc["patch"])
        except Exception as exc:
            rep.fail("%s: patch could not be applied (%s)" % (mc["id"], exc))
            continue
        serrs = schema_errors(validators[schema_of[base]], mutated)
        bviol = []
        if not serrs:
            w2 = dict(world)
            w2[base] = (kind, mutated, cat)
            bviol = business_rules(w2)
        text = " | ".join(serrs + bviol)
        if mc["expect"] == "valid":
            if serrs or bviol:
                rep.fail("%s: expected VALID but got: %s" % (label, text[:300]))
            else:
                counts["valid"] += 1
                rep.ok("%s -> valid, as expected" % label)
        elif mc["stage"] == "schema":
            if not serrs:
                rep.fail("%s: expected a SCHEMA rejection but the mutated record validates" % label)
            elif mc.get("error_contains") and mc["error_contains"] not in text:
                rep.fail("%s: rejected, but not for the expected reason %r: %s" % (label, mc["error_contains"], text[:300]))
            else:
                counts["schema"] += 1
                rep.ok("%s -> rejected by schema" % label)
        else:
            if serrs:
                rep.fail("%s: expected the schema to pass and a business rule to fail, but the schema rejected it: %s" % (label, text[:300]))
            elif not bviol:
                rep.fail("%s: expected a BUSINESS-RULE rejection but nothing failed" % label)
            elif mc.get("error_contains") and not any(mc["error_contains"] in b for b in bviol):
                rep.fail("%s: rejected by %s, expected %s" % (label, sorted({b.split()[0] for b in bviol}), mc["error_contains"]))
            else:
                counts["business"] += 1
                rep.ok("%s -> rejected by %s" % (label, bviol[0].split()[0]))
    print("[5/5] Manifest integrity")
    before = len(rep.failures)
    registered = {fx["file"] for fx in manifest["fixtures"]}
    on_disk = {p.name for p in EXAMPLE_DIR.glob("*.json")}
    for n in sorted(on_disk - registered):
        rep.fail("manifest: %s is in contracts/examples/ but not in fixtures-manifest.json" % n)
    for n in sorted(registered - on_disk):
        rep.fail("manifest: %s is listed but missing on disk" % n)
    ids = [mc["id"] for mc in cases]
    if len(ids) != len(set(ids)):
        rep.fail("manifest: duplicate mutation case ids")
    for fx in manifest["fixtures"]:
        if fx["category"] not in CATEGORIES:
            rep.fail("manifest: %s has unknown category %s" % (fx["file"], fx["category"]))
        obj = world.get(fx["file"], (None, None, None))[1]
        dc = obj.get("data_category") if isinstance(obj, dict) else None
        if dc and dc != fx["category"]:
            rep.fail("manifest: %s category %s differs from its data_category %s" % (fx["file"], fx["category"], dc))
    health = world.get("api-health.json", (None, {}, None))[1]
    if health.get("contract_version") != manifest.get("contract_version"):
        rep.fail("manifest: contract_version differs between fixtures-manifest.json and api-health.json")
    if len(rep.failures) == before:
        rep.ok("manifest, files on disk and categories are consistent")
    online_error = stage_online(rep, world) if args.verify_catalog else False
    print("\nSummary: %d schemas, %d fixtures, business rules BR-01..BR-%d, %d mutation cases "
          "(%d rejected by schema, %d rejected by business rules, %d valid as expected)." %
          (len(schemas), len(world), N_RULES, len(cases), counts["schema"], counts["business"], counts["valid"]))
    print("Scope: structural and cross-file consistency only. This does NOT prove scientific correctness; "
          "scientific review (MH-05 / MH-06 / MH-08) is separate.")
    if not args.verify_catalog:
        print("Note: catalog facts were not compared with live NASA CMR (run with --verify-catalog).")
    if rep.failures:
        print("RESULT: FAIL (%d problem%s)" % (len(rep.failures), "" if len(rep.failures) == 1 else "s"))
        return 1
    if online_error:
        print("RESULT: INCOMPLETE - the online comparison could not be completed.")
        return 2
    print("RESULT: PASS (%d checks)" % rep.passes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
