# ISTMOSAR — JP-06 Technical Review Report

**Subject:** JP-06 API and frontend data contract, `1.0.0-rc.1` · **Reviewed:** October 28, 2026  
**Requested by:** José Peñalba (Technical Director) · **Prepared by:** Claude (AI assistant), working on an uploaded copy of the repository  
**Verdict:** **READY FOR REVIEW** (section G). Human sign-offs, one live-network check and the JP-09 compliance question remain open (section F).

> Scope reminder: this review produced documentation, JSON Schemas, fixtures and a standalone validator only. It built no FastAPI or React application, ran no satellite processing and computed no scientific result.

---

## A. Repository assessment

**How it was inspected.** The upload is a GitHub source archive (`nasaspacechallenge26-main.zip`) with **no `.git` directory**, so `git status` could not be run and uncommitted local changes could not be identified. The archive was treated as the pristine baseline and every change below is measured against it by file comparison. Please run `git status` in the real workspace before applying anything (section I).

**What existed (26 files):** `readme` (no extension); 7 docs including an October 25 JP-06 draft; `references/` (2); `team/` (2); `MH-01-Verification/` (3 CMR search exports); `contracts/schemas/` (7); `contracts/examples/` (3); a 14-line `validate_contracts.py` (it exercised only 3 of the 7 schemas).

**What was missing:** a shared schema and any `$id`; `INSUFFICIENT_EVIDENCE`; a D085 fixture and the study area the NO_GO analysis pointed at; any manifest, negative test or business-rule check; a dependency pin; a contract README; list-response and pagination conventions; an error-code catalogue; a route for serving a Level 1 layer; this review.

**Existing functionality vs proposal.** Nothing in the repository is implemented software. The two verified CMR records are real; everything under `contracts/` is a design artifact. That distinction is preserved in the new documents.

## B. Defects and risks identified

| ID | Class | Finding | Evidence | Resolution |
|---|---|---|---|---|
| C-1 | **Critical** | The D084 fixture `scene-d084.catalog.json`, labelled authentic CMR-derived metadata, carried MD5 `c2099bd62c6be734c93f20e2c61a27f0`. The official CMR record gives `1170fd62056a673656c3824f66dbb671` for D084 (and `f8d31f4b240c78b19e2226a8ed078ed2` for D085); the draft value matches neither. | CMR UMM-JSON for G4371433684-ASF and G4371282627-ASF retrieved 2026-10-28 | Fixture corrected. `--verify-catalog` added; it flags exactly this error (unit-tested). The origin of the draft value is unknown. |
| C-2 | **Critical** | The schemas accepted invalid and fabricated payloads. 8 of 8 probes were **accepted**: a date `"yesterday-ish"`, a truncated granule ID with null CMR ID, a bbox as `[lat, lon, lat, lon]`, west > east, a NO_GO analysis carrying `qa_passed`, computed statistics, `validated_water_change` and a `C:\Users\…` layer URL, one scene listed twice, invented zeros, `source_url: "not a url"`. | probe script against the original schemas | Conditional rules added to the schemas; business rules and 50 mutation tests added. |
| C-3 | **Critical** | Fixture cross-references dangled and nothing checked them: the NO_GO analysis named `area_id: aoi-parita-candidate` and `scene-d085-20261014`, neither of which existed. | `study-area-candidate.json` was `aoi-chagres-gatun-candidate`; no D085 scene file | Parita area and D085 scene fixtures added; BR-01 checks every reference. |
| M-1 | Major | `date-time` and `uri` format keywords were **silently not checked**: without extra packages jsonschema only activates `date`. | probe: active formats `['date']` | `requirements.txt` uses `jsonschema[format-nongpl]`; the validator fails closed if the checkers are missing (tested). |
| M-2 | Major | No `$id` anywhere; relative `$ref`s resolved only through the script's own base URI, so a frontend validator could not resolve them. The script used `RefResolver`, deprecated since jsonschema 4.18. No dependency pin. | schemas, validator source | `$id`-addressed Draft 2020-12 schemas, `referencing` registry, pinned range, local-only reference check, cycle check. |
| M-3 | Major | One `status` mixed decision, lifecycle and approval; `INSUFFICIENT_EVIDENCE` was missing; reasons were free text. | draft `analysis.status`, `pair_assessment` | Three independent axes plus 12 machine-readable checks. |
| M-4 | Major | Layers mixed the scientific artifact with the browser representation (`format` listed `geotiff` beside `tile_xyz`); one `url`; bounds order undocumented; no pixel spacing, no availability. | draft `layer.schema.json` | `raster` (artifact) vs `delivery` (EPSG:3857 overlay or XYZ tiles); GeoTIFF can never be a delivery method. |
| M-5 | Major | Statistics lacked total and invalid pixels, the threshold and its unit, area CRS and any nullability rule. | draft `statistics.schema.json` | Rebuilt; `UNAVAILABLE` forces every number to `null`; area never from degree spacing. |
| M-6 | Major | Provenance could not reproduce a result: no retrieval info, CRS, resampling, grid alignment, masking, outputs or reviewer. | draft `provenance.schema.json` | Structured `sources`, `processing`, `outputs`, `review`; closed parameter/software sets. |
| M-7 | Major | Scene lacked cycle, orbit, mode, frequency and maturity as fields; "verified polarizations" used `HH` names, not dataset names; `cmr_concept_id` was optional. | draft `scene.schema.json` | Per-frequency nominal vs HDF5-verified covariance terms; official IDs required unless simulated. |
| M-8 | Major | Level 1 had **no route** to serve a scene's layer (`/layers` existed only under analyses). | seven conceptual routes | Added `GET /api/scenes/{id}/layers` and `GET /api/scenes/{id}`, clearly flagged as a review addition. |
| M-9 | Major | No list-response, pagination, versioning or error-code convention. | draft §2 | Single envelope, `limit/offset`, version in `/health`, envelopes and header; 8-code error table with enforced HTTP status. |
| M-10 | Major | The three `MH-01` exports are not exhaustive: every query used `page_size=10`, so each file is page 1 only (2026-06-16 → 2026-07-05, **no October record at all**). | query strings in each file | Recorded in section H; nothing concluded from absence. |
| m-1 | Minor | Redundant method value: `pairwise_log_ratio` equals `delta_db` (log ratio = difference of logs). | draft enum | Single `PAIRWISE_DELTA_DB`. |
| m-2 | Minor | Draft fixture truncated the official end time to `…17.999Z`. | CMR `…17.999342Z` | Official values kept verbatim. |
| m-3 | Minor | Parts of the draft inferred facts from file-name tokens. CMR shows `J` in both names while `JOINT_OBSERVATION` is TRUE for D084 and FALSE for D085. | UMM attributes | Rule: use catalog attributes where they exist; treat name tokens as nominal. |
| m-4 | Minor | `references/Evidence-Index.md` contains two local paths with a personal user name (`C:\Users\…\Downloads\…`) in a public repository. | lines 16–17 | Not changed (approved JP-05 file). Recommendation R-3. |
| R-1 | Recommendation | Add a `.gitignore` (`*.h5`, `.env`, `__pycache__/`, `*.zip`) to honour the "no HDF5 / no credentials in Git" rule. | no `.gitignore` | Not added (outside JP-06 scope). |
| R-2 | Recommendation | Rename `readme` to `README.md` so GitHub renders it. | root listing | Not changed. |
| R-3 | Recommendation | Index the three MH-01 exports in `Evidence-Index.md` as raw, unreviewed search exports, and replace the local paths with a neutral description. | section H | Not changed (JP-05 owns it). |
| R-4 | Recommendation | Run `python validate_contracts.py --verify-catalog` once on a networked machine and commit nothing that fails it. | sandbox could not reach CMR | Open. |
| R-5 | Recommendation | Smoke-test the schemas with the actual frontend validator (for example Ajv 2020 with `ajv-formats`). | not available here | Open (JP-07/JP-08). |

## C. Files created or modified

**Created (21):**

| Path | Purpose |
|---|---|
| `contracts/schemas/common.schema.json` | shared ids, UTC timestamp, lon/lat types, enums, review record, processing parameters |
| `contracts/schemas/api-responses.schema.json` | health response, pagination info, four list envelopes |
| `contracts/fixtures-manifest.json` | fixture → schema + category registry; 50 mutation cases |
| `contracts/requirements.txt` | `jsonschema[format-nongpl]>=4.18,<5` |
| `contracts/README.md` | layout, how to run, how to extend |
| `contracts/examples/scene-d085.catalog.json` | authentic D085 record; a scene without an extracted layer |
| `contracts/examples/study-area-gulf-of-parita-candidate.json` | the area the NO_GO analysis references |
| `contracts/examples/study-area-sim-training-box.simulated.json`, `scene-sim-earlier/later.simulated.json`, `analysis-sim-go-completed.simulated.json`, `analysis-sim-insufficient-evidence.simulated.json`, `layer-sim-before/after/change.simulated.json` | SIMULATED_DATA optional-field and state examples |
| `contracts/examples/api-health.json`, `api-scenes-list.json`, `api-layers-list-empty.json` | envelope, health, empty-result behavior |
| `contracts/examples/error-incompatible-observations.json`, `error-resource-not-found.json` | failed layer request; unknown id |
| `docs/JP-06-Review-Report.md` | this report |

**Modified (13):**

| Path | Change |
|---|---|
| `contracts/schemas/` — the seven existing schemas: `study-area`, `scene`, `layer`, `analysis`, `statistics`, `provenance`, `error` (each `*.schema.json`) | rebuilt as `$id`-addressed Draft 2020-12 schemas with conditional rules (section D) |
| `contracts/examples/scene-d084.catalog.json` | MD5 corrected; official microsecond times; new fields |
| `contracts/examples/analysis-d084-d085-NO-GO.json` | 12 machine-readable checks; references now resolve; statistics `UNAVAILABLE` |
| `contracts/examples/study-area-candidate.json` | country, purpose, evidence references, category |
| `docs/JP-06-API-Data-Contract.md` | full rewrite as v1.0.0-rc.1 (migration table in §12) |
| `docs/System-Architecture.md` | 2 localized edits (+3/−3 lines): pointer to the contract; the informal analysis sketch marked superseded |
| `validate_contracts.py` | rewritten (14 → 812 lines) |

**Deliberately untouched (byte-identical to the upload):** `docs/MVP-Requirements.md`, `Backlog-and-Integration.md`, `Stage-0-Decisions.md`, `Current-Blockers.md`, `Challenge-Rules.md`, `references/*`, `team/*`, `readme`, and all three `MH-01-Verification/*.json`.

## D. Data-contract decisions

| Topic | Decision and reason |
|---|---|
| Version | `1.0.0-rc.1`. The draft was unfrozen and never implemented; a release-candidate label signals "pending sign-off". Schemas are addressed by `$id`, not by file name. |
| Identifiers | internal lowercase slugs; official granule and CMR IDs stored verbatim in their own fields. A pattern rejects truncated granule IDs. |
| Statuses | decision / evidence level / lifecycle / approval are separate. A GO at catalog level is preliminary; `COMPLETED` is not approval. |
| Compatibility | 12 named checks with `PASS`/`FAIL`/`NOT_EVALUATED`; the decision must be consistent with them (BR-06). Same cycle + same track = one pass, never a before/after pair (BR-05). |
| Timestamps | UTC with `Z`, up to 6 fractional digits (official CMR values kept as they are); reviews use dates (`reviewed_on`) rather than invented times of day. |
| Geography | lon/lat everywhere; CMR's latitude-first polygons are converted; schema checks shape, BR-04 catches swapped Panama coordinates. |
| Measurements | `GAMMA0`/`SIGMA0` explicit; Δ is later minus earlier with `10·log10(P)` on finite positive linear power; earlier/later ids are recorded because the sign depends on them. |
| Layers | scientific artifact (`raster`) separated from browser representation (`delivery`: reprojected overlay or XYZ tiles in EPSG:3857). No local paths ever reach the frontend. |
| Statistics | `null` = not computed; `UNAVAILABLE` forces all numbers null; area from degree spacing is a rule violation. |
| Provenance | no secrets possible: `parameters` and `software` are closed sets with restricted values. |
| API shape | lists return one envelope; single resources return bare objects; empty = `200`; role-filter errors explain *why* a result is absent. |
| Errors | eight codes with enforced HTTP status; messages are user-safe; errors never carry science. |
| Categories | VERIFIED_METADATA / PROPOSED_STRUCTURE / SIMULATED_DATA / UNAVAILABLE as requested, plus a reserved `PROCESSED_NISAR_DATA` so real outputs can eventually be expressed without relabelling simulations. |
| Claim level | only `CATALOG_ONLY` and `RADAR_BACKSCATTER_CHANGE`; no flood-confirming value can validate. |

**Judgement calls José may override:** the `rc.1` label; the added scene routes; uppercase enums; the `data_category` field on production objects; `SAME_FRAME` as an MVP check (adjacent-frame mosaicking out of scope); the Panama plausibility envelope (lon −83.5…−77.0, lat 7.0…10.0, intentionally generous). The NO_GO fixture records José as approving on 2026-10-25 (the date of the Stage 0 decision log, DEC-005); please confirm that attribution.

## E. Validation evidence

All commands were executed in a Linux sandbox with Python 3.12.3, `jsonschema 4.26.0`, `referencing 0.37.0`, `rfc3339-validator 0.1.4`, `rfc3986-validator 0.1.1`.

| # | Command / action | Result |
|---|---|---|
| 1 | `python3 validate_contracts.py` on the **original** repository | exit 0, with a `RefResolver` DeprecationWarning; it validated 3 fixtures against 3 schemas (study-area, scene, analysis). The layer, statistics, provenance and error schemas were never exercised |
| 2 | probe script: 8 invalid payloads against the original schemas | **8 of 8 accepted**; active format checkers: `['date']` only |
| 3 | `pip install "jsonschema[format-nongpl]>=4.18,<5"` | `date-time`, `uri`, `date` active |
| 4 | `python3 -W error validate_contracts.py` (refined) | **exit 0** · 9 schemas, 18 fixtures, BR-01…BR-15, 50 mutation cases (**30 rejected by schema, 18 rejected by business rules, 2 valid as expected**) · **81 checks passed** · no warnings |
| 5 | same, run from `/` instead of the repo root | PASS (81 checks) |
| 6 | per-case review of all 50 mutations | each rejection occurs for its **intended** reason (first error printed and read for every case) |
| 7 | negative control T1: add a layer id to the NO_GO analysis | exit 1; schema failure plus BR-01 and BR-09 |
| 8 | negative control T2: unregistered file in `examples/` | exit 1 |
| 9 | negative control T3: `$ref` to a missing definition | exit 1, `unresolvable $ref` |
| 10 | negative control T4: uninstall `rfc3339-validator` and `rfc3986-validator` | exit 1: `format checkers missing for date-time, uri`. (My first attempt did not actually uninstall them and wrongly passed; I redid it with `--break-system-packages` and verified the packages were gone.) |
| 11 | JSON hygiene over all 28 JSON files in `contracts/` | all parse; no BOM, no CRLF, no duplicate keys |
| 12 | cross-document check (counts, file references, test ids, contract version) | consistent after two wording fixes it found ("five counts" → four; `NEG-11…15` → `NEG-11…14`) |
| 13 | official CMR records G4371433684-ASF and G4371282627-ASF retrieved (twice each) and compared with the fixtures | granule ID, times, size, MD5, footprint, track, frame, direction, coverage, orbit, product version, update date and QA URLs **all match** |
| 14 | unit tests of `compare_scene_with_umm` against stubs transcribed from those fresh readings | fixtures match; the old MD5, a swapped footprint, wrong track/coverage, a changed update date and a mistyped QA URL are each detected |

**Not executed, so not claimed:** the live `--verify-catalog` network path (the sandbox cannot reach `cmr.earthdata.nasa.gov`; only the comparison logic was tested); Windows, and Python 3.10/3.11 (requirements state 3.10+ but I ran 3.12 only); Ajv or any JavaScript validator; any `git` command. A passing run proves structure and cross-file consistency, **not** scientific correctness.

## F. Remaining dependencies

| Area | Open items |
|---|---|
| **Scientific data availability** | BL-01: no accepted different-date pair. MH-05/MH-06 must review the candidates in section H. The October 12 lead `G4364362137-ASF` (track 004, ascending, EV-CMR-003) still needs its frame and footprint. |
| **Scientific processing** | MH-07 runbook and MH-08 QC checklist; real HDF5 inspection (so `covariance_terms_verified` can be filled); real QA review; product known-issues check; real alignment and valid-pixel overlap. None of this exists yet, and the fixtures say so. |
| **Frontend / backend implementation** | not started and not authorized. The contract only specifies the future behavior (including "availability must reflect real artifact existence"). |
| **Competition-rule approval (JP-09)** | The rules on pre-event development, reuse and prepared datasets are unresolved (BL-03). **Flag for organizer clarification:** *"May a team publish JSON schemas, example payloads and a standalone validator for its planned data interface before the event, and may that material be reused during the event?"* Compliant fallback: keep these files private as design notes until answered, and build nothing application-level before then. |
| **Team review** | Maryfer: check semantics, units and the area method. Xavier: UI assumptions. José: decide the open judgement calls (section D), keep or drop `GET /api/scenes/{id}/layers`, confirm the NO_GO attribution, and bump to `1.0.0`. |

## G. JP-06 acceptance assessment

| Requirement | Status | Basis |
|---|---|---|
| Satellite-scene structure defined | Satisfied | `scene.schema.json`; nominal vs inspected channels; catalog vs verified checksum |
| Analysis structure defined | Satisfied | `analysis.schema.json`; decision / lifecycle / approval separated |
| Geographic-layer references defined | Satisfied | `layer.schema.json`; artifact vs delivery; no local paths |
| Statistics format defined | Satisfied | `statistics.schema.json`; nullability rule; area rules |
| Provenance and scientific limitations defined | Satisfied | `provenance.schema.json`; mandatory `limitations[]` on scene, layer and analysis |
| API endpoints documented | Satisfied | contract §5: parameters, responses, errors, empty results, pagination, frontend use |
| JSON examples structurally validated | Satisfied | evidence rows 4–6 |
| Documentation internally consistent | Satisfied, self-checked | evidence rows 11–12; a human read is still needed |
| No fabricated scientific results | Satisfied | the only numeric statistics are in files named `.simulated.`, categorised `SIMULATED_DATA`, dated 2000, located near 0°N 0°E, with `example.invalid` URLs |
| No unauthorized competition implementation | Satisfied, with an open question | no application, processing or deployment code; whether pre-event schemas are themselves allowed is the JP-09 question above |

**Conclusion: READY FOR REVIEW.** Not `1.0.0`: the human reviews and the networked `--verify-catalog` run (R-4) are still outstanding.

## H. Handoff to Maryfer — MH-05 / MH-06 (UNREVIEWED catalog observations)

These are **observations from catalog metadata only**. Nothing here is a GO, an approved pair or a scientific result, and none of it was written into the fixtures.

**What the three exports are.** 23 unique records (30 entries, 7 repeated across files), all from page 1 of a `page_size=10` query, dates 2026-06-16 → 2026-07-05, **no October record**. They cannot show that a pair does or does not exist for October; a new search (larger page size or a date range including October) is needed.

**Catalog footprints** (equal-area projection, catalog polygons only): D084 ≈ 57,865 km², D085 ≈ 30,608 km². They overlap by ≈ 3,399 km² (11.1% of D085, 5.9% of D084), so the adjacent frames share a narrow strip. That is geometric overlap, not temporal independence. Share of each candidate box covered by a single frame:

| Study-area box | D084 | D085 |
|---|---|---|
| Chagres / Gatún | 95.5% | 0.0% |
| Gulf of Parita | 67.8% | 42.2% |
| Chiriquí / David | 0.0% | 0.0% |

**Same track / direction / frame / mode / nominal channels, different dates** (the "tail" token is the orbit-accuracy character of the file name; coverage F = full, P = partial):

| Group | Records |
|---|---|
| track 040 D, frame 084, 4005, DHDH | `G4250187623-ASF` cycle 023, 2026-06-16, accuracy **F**, full · `G4240958164-ASF` cycle 024, 2026-06-28, accuracy N, full |
| track 040 D, frame 085, 4005, DHDH | `G4250162186-ASF` 06-16, **F**, partial · `G4251853228-ASF` 06-28, N, partial |
| track 069 D, frame 084, 4005 | `G4254542991-ASF` 06-19 · `G4251917498-ASF` 07-01 (both N, full) |
| track 141 D, frame 084, 4005 | `G4244059874-ASF` 06-23 · `G4245663416-ASF` 07-05 (both N, full) |
| track 076 A, frames 005 and 006, 4005 | partial coverage on both dates (frame 006 appears twice per date) |
| tracks 076 A frame 007 and 141 D frame 083 | mode `0005 NADV`: a different mode and polarization, **not** comparable with HH/HV 4005 |

**Candidates against D084 (2026-10-14, cycle 033, accuracy N, full):**

| Record | Date | Interval | Orbit-accuracy token | Footprint IoU with D084 | Common coverage of Chagres / Parita boxes |
|---|---|---|---|---|---|
| `G4240958164-ASF` | 2026-06-28 | 108 days (9 cycles) | N (same as D084) | 0.971 | 95.5% / 67.8% |
| `G4250187623-ASF` | 2026-06-16 | 120 days (10 cycles) | **F** (differs) | 0.970 | 95.5% / 67.8% |

On catalog evidence alone, `G4240958164-ASF` is the more consistent candidate to review first. This is a review priority, **not** an approval.

**Not established (all of it must be checked before any GO):** valid-pixel overlap; that the HH/HV datasets actually exist in each HDF5; product version and orbit type of the June records (the search export has no UMM attributes; the UMM `STACK_ID` such as `040_D_084` would give a direct same-geometry test); whether the `F` orbit-accuracy token implies poorer geolocation for the June 16 record; product known issues for PROVISIONAL data; NASA QA reports; wet-season context (both dates are in the Panama rainy season, which affects any interpretation but not compatibility); the October 12 lead's frame (the Chiriquí export holds track 004 ascending frames 005, partial, and 006, full, dated 2026-06-26, which would be the natural counterpart if the lead sits on one of those frames; unconfirmed). Two oddities to look at: two granules carry the same track, frame and date 16 seconds apart (track 076 A frame 006), and frame 085 on 2026-06-23 appears in modes 4005 and 2005 at the same start time. One open question for MH-08: the file-name accuracy token is `N` for D084/D085 while CMR reports `ORBIT_TYPE = MOE`; how the two relate was not established.

## I. Git and workspace notes

No Git command was run (the upload has no `.git`). Nothing was committed or pushed; the diff was reviewed by comparing every file with the original archive (section C). In your workspace, suggested steps (run `git status` first and keep any uncommitted work of your own):

```text
git status
pip install -r contracts/requirements.txt
python validate_contracts.py
git add contracts docs/JP-06-API-Data-Contract.md docs/JP-06-Review-Report.md docs/System-Architecture.md validate_contracts.py
git diff --staged --stat
git commit -m "docs: refine ISTMOSAR JP-06 API and scientific data contracts"
```

Wait for José's approval before committing. No credentials, tokens or HDF5 files are included; the validator reads only repository files unless `--verify-catalog` is passed.
