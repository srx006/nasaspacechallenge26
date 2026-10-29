# ISTMOSAR — JP-06 API and Frontend Data Contract v1.0.0-rc.1

**Owner:** José Peñalba · Space Dogs / ARPIP  
**Draft prepared:** October 25, 2026 · **Refined:** October 28, 2026 · **Target review:** October 29, 2026  
**Contract version:** `1.0.0-rc.1` (release candidate; becomes `1.0.0` only after the sign-offs in §13)  
**Status:** PROPOSED CONTRACT — planning specification. **Not a deployed API and not an implemented application.**  
**Normative files:** `contracts/schemas/*.schema.json` (JSON Schema Draft 2020-12). Where this document and a schema disagree, the schema wins and this document is wrong.  
**Aligned with:** `docs/MVP-Requirements.md`, `docs/System-Architecture.md`, `docs/Stage-0-Decisions.md`, `docs/Current-Blockers.md`, `references/Evidence-Index.md`.

---

## 0. Compliance boundary (JP-09)

The governing event rules on pre-event development, reuse of existing code and prepared datasets are **not yet confirmed** (`BL-03`). Until JP-09 is resolved, this work is limited to:

- architecture research, documentation, JSON Schema definitions and example fixtures;
- one standalone offline validator (`validate_contracts.py`) that reads only files inside this repository.

It deliberately does **not** include a FastAPI or React application, satellite processing code, a deployed service, or any computed satellite result. Whether *schema and fixture designs prepared before the event* count as "prepared work" under the rules is itself an open question and is **flagged for organizer clarification** (see `docs/JP-06-Review-Report.md`, section F). Recommended compliant position: keep these files as design documentation, and build the implementation only after JP-09 authorizes it.

## 1. Objective and scope

Define, without ambiguity, the data exchanged between the scientific processing step, the future FastAPI backend and the React/Leaflet/Chart.js frontend:

```
NASA/ASF NISAR L2 GCOV  →  Python geospatial processing  →  FastAPI (JSON)  →  React / Leaflet / Chart.js
```

| Level | What the contract must carry | Requirement |
|---|---|---|
| 1 — Radar Explorer | one authentic scene, its provenance, a georeferenced radar layer, legend, limitations | FR-01, FR-02, FR-03 |
| 2 — Change Explorer | two compatible scenes, compatibility decision with reasons, before/after/change layers, valid-pixel statistics, provenance, limitations | FR-04 … FR-09 |

**Out of scope for v1.0.0-rc.1:** Level 3 water interpretation, Level 4 wetland classification, sensors, AI features. A radar backscatter change is **not** evidence of flooding, water depth, deforestation or ground deformation, so the contract has no field that can express a confirmed flood (see `scientific_claim_level`, §4.D).

**Current factual state:** the two verified October 14 granules (D084, D085) are **not** a temporal pair. No compatible different-date pair is approved (`BL-01`). Every fixture respects this.

## 2. Global conventions

| Topic | Rule |
|---|---|
| Format | JSON, UTF-8 **without BOM**, LF line endings. (The three `MH-01-Verification/*.json` exports contain a BOM; the validator tolerates it but warns.) |
| Identifiers | Internal `id` values match `^[a-z0-9][a-z0-9-]{2,79}$`. They are never file paths. Official identifiers (granule ID, CMR concept ID) are stored **unmodified** in their own fields. |
| Timestamps | RFC 3339 **UTC with a trailing `Z`** (`2026-10-14T23:44:44.000000Z`). Up to 6 fractional digits allowed so official CMR values are kept verbatim. Numeric offsets (`+00:00`) are rejected. Dates without time use `YYYY-MM-DD` (`*_on` fields). |
| Geographic coordinates | **Longitude first**: positions are `[longitude, latitude]`; boxes are `[west, south, east, north]`; all in EPSG:4326 decimal degrees. |
| NASA CMR polygons | CMR `polygons` strings and UMM `Points` are **latitude-first**. They must be converted when building a footprint (the fixtures already are). Leaflet bounds are `[[south, west], [north, east]]`: the frontend converts from `[west, south, east, north]`. |
| Coordinate checks | JSON Schema checks ranges and array shape. It cannot detect a swapped Panama pair (`[8.8, -80.5]` is a legal lon/lat). Business rule BR-04 catches this with a Panama plausibility envelope. |
| Enumerations | `UPPER_SNAKE_CASE`, except units (`dB`, `linear_power`, `dimensionless`, `m`, `deg`) and polarization/channel names that are NASA vocabulary (`HH`, `HHHH`). |
| Nullability | `null` means **not computed / not known / not applicable**. It never means zero. A field that is required is always present; "unknown" is expressed as `null` only where the schema allows it. Computed counts of `0` are legitimate only when computed. |
| URLs | Absolute `https://` only. Local paths (`C:\…`, `/home/…`), `file://` and `s3://` are rejected by schema; the frontend never receives them. |
| Secrets | No tokens, passwords or Earthdata credentials anywhere. Processing `parameters` and `software` are closed sets, so a credential field cannot validate. |
| Versioning | Semantic version. Schemas declare `$id = https://spacedogs.example/istmosar/contracts/v1/<name>.schema.json` (`.example` is a reserved, non-resolvable namespace: an identifier, not a download location). The version is exposed in `/health`, in every list envelope, and in the `X-ISTMOSAR-Contract-Version` response header. Breaking changes require a major bump (and then a deliberate decision on an `/api/v2` prefix). |

## 3. Status model and data categories

Three **independent axes** replace the single mixed `status` of the draft. A preliminary GO is therefore never mistaken for finished science.

| Axis | Field | Values | Meaning |
|---|---|---|---|
| Compatibility | `analysis.compatibility.decision` | `PENDING`, `GO`, `NO_GO`, `INSUFFICIENT_EVIDENCE` | Can these two scenes be compared at all? |
| Evidence behind it | `analysis.compatibility.evidence_level` | `NONE`, `CATALOG_METADATA`, `HDF5_METADATA`, `PIXEL_CHECKS_PASSED` | A GO at `CATALOG_METADATA` is **preliminary**, never validation. |
| Lifecycle | `analysis.lifecycle_status` | `NOT_STARTED`, `PLANNED`, `PROCESSING`, `COMPLETED`, `FAILED` | Where is the processing? `COMPLETED` does not mean approved. |
| Approval | `analysis.approval.status` | `NOT_REVIEWED`, `IN_REVIEW`, `APPROVED`, `REJECTED` | Has a human accepted it? |

Other state fields: scene `catalog_status` (`CANDIDATE`/`CATALOG_VERIFIED`/`REJECTED`), `hdf5_inspection.status`, `extraction_status`, `quality_review`; layer `availability` (`NOT_GENERATED`/`AVAILABLE`/`WITHDRAWN`) and `quality_status` (`NOT_ASSESSED`/`IN_REVIEW`/`PASSED`/`FAILED`); provenance `status` (`NOT_STARTED`/`PLANNED`/`EXECUTED_UNVERIFIED`/`VERIFIED`/`FAILED`).

**Data categories** (`data_category`; also the fixture classification). They must never be confused:

| Category | Meaning | Allowed on |
|---|---|---|
| `VERIFIED_METADATA` | Based on an independently checked official NASA record | scene, analysis (decision resting on verified metadata only) |
| `PROPOSED_STRUCTURE` | Design example or team-defined object | study area, scene (unchecked candidate), API/error examples |
| `SIMULATED_DATA` | Artificial; training or structural testing only; never satellite data | any resource; file name contains `.simulated.`; URLs use `example.invalid` |
| `UNAVAILABLE` | A scientific result that has not been generated | layer, statistics |
| `PROCESSED_NISAR_DATA` | **Reserved** for real, provenance-backed outputs. No fixture uses it. | analysis, layer, statistics |

## 4. Entity contracts

The tables are explanatory. Types, ranges, enums and conditional rules are in the schemas.

### A. Study Area — `study-area.schema.json`

| Field | Notes |
|---|---|
| `id`, `data_category` | `PROPOSED_STRUCTURE` or `SIMULATED_DATA` (areas are never "verified metadata") |
| `name`, `country` (ISO 3166-1 alpha-2; `XX` only if simulated), `region` | human-readable |
| `bbox_lonlat` | `[west, south, east, north]` |
| `crs` | constant `EPSG:4326` |
| `geometry` | optional GeoJSON Polygon, lon/lat order, or `null` |
| `selection_status` | `CANDIDATE` / `APPROVED` / `REJECTED`. `APPROVED` requires at least one `evidence_refs` entry. A candidate is **not** an approved scientific case. |
| `scientific_purpose` | why this area |
| `evidence_refs[]` | `{kind: EVIDENCE_INDEX_ID \| REPOSITORY_PATH \| URL, ref, note}` |

### B. Satellite Scene — `scene.schema.json`

| Group | Fields |
|---|---|
| Identity | `id`; `cmr_concept_id` (official, required unless simulated); `granule_id` (complete producer granule ID, pattern-checked, truncated IDs rejected); `collection`, `collection_concept_id`; `product` (`L2_GCOV`); `product_maturity` (`BETA`/`PROVISIONAL`/`VALIDATED`); `product_version`, `crid` (nullable if the catalog export lacks them) |
| Time | `acquisition_start_utc`, `acquisition_end_utc` |
| Geometry of observation | `direction` (`ASCENDING`/`DESCENDING`), `cycle`, `track`, `frame`, `orbit_number`, `frame_coverage` (`FULL`/`PARTIAL`) |
| Radar | `radar_band` (`L`), `radar_mode_code` (e.g. `4005` = 40 MHz + 5 MHz), `frequencies[]` = `{band A/B, range_bandwidth_mhz, polarizations_nominal[], covariance_terms_verified[]}` |
| Footprint | `footprint` GeoJSON Polygon lon/lat or `null` |
| Catalog | `source_url` (official CMR UMM-JSON URL), `catalog_updated_utc`, `catalog_verified_on`, `official_qa_references[]` |
| File | `file` = `{name, size_bytes, catalog_checksum {MD5}, download_verification {NOT_DOWNLOADED/VERIFIED/MISMATCH, sha256, verified_at_utc}}` or `null` |
| States | `catalog_status`, `hdf5_inspection {status, inspected_at_utc, inspected_by}`, `extraction_status`, `raster_layer_id`, `quality_review`, `provenance` (null until extraction) |
| Honesty | `limitations[]` (at least one), optional `notes[]` |

**Nominal versus inspected channels.** `polarizations_nominal` comes from the catalog or file name. `covariance_terms_verified` lists only HDF5 datasets that were actually found, and **must be empty while `hdf5_inspection.status` is `NOT_INSPECTED`** (schema-enforced). Likewise `catalog_checksum` is what CMR declares; `download_verification` records whether a local file was ever compared with it. `quality_review` is separate from catalog authenticity: an authentic record can still have unusable pixels.

### C. Geographic Layer — `layer.schema.json`

| Group | Fields |
|---|---|
| Identity | `id`, `data_category` (`UNAVAILABLE`/`SIMULATED_DATA`/`PROCESSED_NISAR_DATA`), `parent {type SCENE\|ANALYSIS, id}`, `role` (`SCENE_BACKSCATTER`, `BEFORE`, `AFTER`, `CHANGE`, `CHANGE_MASK`, `VALID_MASK`, `CONTEXT`), `purpose`, `source_scene_ids[1..2]` |
| State | `availability` (reflects whether the artifact really exists), `quality_status` |
| Measurement | `measurement {convention GAMMA0\|SIGMA0\|NOT_APPLICABLE, unit dB\|linear_power\|dimensionless, covariance_term, frequency_band}` |
| Scientific artifact | `raster` (or `null`) = `{format GEOTIFF\|COG, crs, bounds_lonlat, grid {width_px, height_px, pixel_size_x/y, pixel_size_unit m\|deg}, nodata {representation NAN\|VALUE\|MASK_BAND, value, policy}, artifact_id, download_href, sha256}` |
| Frontend representation | `delivery` (see §6) |
| Other | `legend`, `provenance_id`, `limitations[]` |

Role rules enforced by schema: `BEFORE`/`AFTER`/`CHANGE`/`SCENE_BACKSCATTER` need a real convention (`GAMMA0`/`SIGMA0`), a diagonal covariance term and a frequency band; `CHANGE` is in `dB` and cites **two** scenes; `BEFORE`/`AFTER`/`SCENE_BACKSCATTER` cite **one**; masks are `dimensionless`. An `AVAILABLE` layer must have a `raster` and a delivery method; a non-available layer must have `raster: null`, delivery `NONE` and category `UNAVAILABLE`.

### D. Scientific Analysis — `analysis.schema.json`

| Group | Fields |
|---|---|
| Identity | `id`, `data_category`, `area_id`, `scene_ids` (exactly two, **distinct**) |
| Time | `temporal_relationship {classification SAME_ACQUISITION\|DISTINCT_ACQUISITIONS\|UNDETERMINED, earlier_scene_id, later_scene_id, interval_seconds}` |
| Decision | `compatibility {decision, evidence_level, summary, checks[12], assessed_by, assessed_on}` |
| Method | `selected_channel {covariance_term, frequency_band}` or `null`; `measurement_convention` or `null`; `processing_method` or `null` (`PAIRWISE_DELTA_DB`, `LATER_MINUS_EARLIER`, `10*log10(P)`, `FINITE_POSITIVE_LINEAR_POWER`); `parameters` |
| Results | `lifecycle_status`, `layer_ids[]` (full layers via `/layers`), `statistics`, `provenance` (both embedded, each with its own `id`) |
| Claim | `scientific_claim_level`: `CATALOG_ONLY` or `RADAR_BACKSCATTER_CHANGE`. Water/flood claim levels are an optional later extension. |
| Honesty / review | `limitations[]`, `approval`, `reference_urls[]` |

**The 12 compatibility checks** (each exactly once, `result` = `PASS`/`FAIL`/`NOT_EVALUATED`):
catalog level — `TEMPORAL_INDEPENDENCE`, `SAME_TRACK`, `SAME_DIRECTION`, `SAME_FRAME`, `SAME_RADAR_MODE`, `COMPATIBLE_MATURITY_AND_VERSION`, `CATALOG_FOOTPRINT_OVERLAP`; HDF5 level — `CHANNEL_VERIFIED_IN_BOTH`, `SAME_MEASUREMENT_CONVENTION`; pixel level — `VALID_PIXEL_OVERLAP`, `GRID_ALIGNMENT`; human — `QUALITY_REVIEW`.
`SAME_FRAME` is an MVP simplification (same track/direction/frame); mosaicking adjacent frames is out of scope.

**Decision semantics**

| Decision | Rule | Consequence (schema-enforced) |
|---|---|---|
| `NO_GO` | at least one check is `FAIL` | no layers, statistics `UNAVAILABLE`, claim `CATALOG_ONLY`, no channel/method, lifecycle `NOT_STARTED` |
| `INSUFFICIENT_EVIDENCE` | no `FAIL`, but a catalog-level check is `NOT_EVALUATED` | same as `NO_GO` |
| `PENDING` | assessment not done: every check `NOT_EVALUATED`, evidence `NONE` | no results; lifecycle `NOT_STARTED` or `PLANNED` |
| `GO` | no `FAIL`, every catalog-level check `PASS` | may proceed; **GO at `CATALOG_METADATA` is preliminary** |

`lifecycle_status = COMPLETED` additionally requires: decision `GO`, evidence `PIXEL_CHECKS_PASSED`, computed statistics, at least one layer, a channel, convention and method, provenance `EXECUTED_UNVERIFIED` or `VERIFIED`, claim `RADAR_BACKSCATTER_CHANGE`. An `APPROVED` GO analysis additionally requires `QUALITY_REVIEW = PASS` and an `APPROVED` provenance review. Completed ≠ approved.

`temporal_relationship`: scenes with the **same cycle and the same track are one acquisition pass** (`SAME_ACQUISITION`) and can never be a before/after pair. `earlier_scene_id`/`later_scene_id` exist because the sign of Δ depends on them.

### E. Statistics — `statistics.schema.json`

| Field | Meaning |
|---|---|
| `data_category` | `UNAVAILABLE` (nothing computed), `SIMULATED_DATA`, `PROCESSED_NISAR_DATA` |
| `total_pixels_inspected` | pixels on the aligned grid = valid + invalid |
| `valid_pixel_count` | finite, positive, unmasked in **both** scenes |
| `invalid_pixel_count` | excluded: nodata, mask-invalid, non-positive or non-finite in either scene |
| `changed_pixel_count`, `changed_pixel_pct` | valid pixels with \|Δ\| ≥ threshold; `100 × changed / valid` (null if valid = 0) |
| `mean_delta_db` | mean Δ (later − earlier) over **all valid** pixels, in dB |
| `change_threshold` | `{value > 0, unit "dB", rule "ABS_DELTA_GTE"}` |
| `changed_area_km2`, `area_method`, `area_crs` | square kilometres; `EQUAL_AREA_GRID`, `GEODESIC_PER_PIXEL`, `UTM_PLANIMETRIC_APPROX` or `NOT_CALCULATED` |
| `qc_notes[]` | quality-control remarks |

**Nullability rule:** `UNAVAILABLE` ⇒ every numeric field `null` and `area_method = NOT_CALCULATED` (schema-enforced). Any other category ⇒ the four pixel counts (total, valid, invalid, changed) and the threshold are mandatory. **Area is never computed from degree pixel spacing**: BR-08 rejects an area method on a grid whose spacing unit is `deg`.

### F. Scientific Provenance — `provenance.schema.json`

`id`, `status`, `sources[]` (per scene: official granule ID, CMR concept ID, catalog URL, collection, maturity, `retrieval {status, method, retrieved_at_utc}`, `dataset_paths_inspected[]` — HDF5 paths actually opened, empty if none — catalog checksum, local SHA-256), `processing` (`null` until processing exists: selected channel, convention, source and destination CRS, resampling method, `grid_alignment`, `masking_rules[]`, `parameters`, `software` name→version map, start/end timestamps), `outputs[]` (artifact IDs, kind, SHA-256), `quality_checks[]`, `review`. Statuses `NOT_STARTED`/`PLANNED` cannot carry processing details or outputs; `VERIFIED` requires an `APPROVED` review. `parameters` is a closed set (`change_threshold_db`, `threshold_rule`, `use_product_mask`, `subset_bbox_lonlat`, `speckle_filter`) and `software` values are version strings only, so credentials cannot be stored.

HDF5 dataset paths follow the NASA/ASF GCOV layout `/science/LSAR/GCOV/grids/frequency{A|B}/{HHHH|HVHV|…}`. The schema accepts only that shape.

### G. API Errors — `error.schema.json`

```json
{ "error": { "code": "INCOMPATIBLE_OBSERVATIONS", "message": "…", "http_status": 409, "detail": { "…": "optional" } } }
```

| `code` | HTTP | When |
|---|---|---|
| `RESOURCE_NOT_FOUND` | 404 | unknown study area, scene or analysis (including an unknown `area_id` filter) |
| `INVALID_PARAMETER` | 422 | malformed path/query parameter |
| `INVALID_SCENE_PAIR` | 422 | `scene_ids` filter that is not exactly two distinct ids |
| `INCOMPATIBLE_OBSERVATIONS` | 409 | a result is requested from an analysis whose decision is `NO_GO` |
| `UNVERIFIED_DATA` | 409 | a result is requested from an analysis that is `PENDING` or `INSUFFICIENT_EVIDENCE` |
| `LAYER_NOT_GENERATED` | 409 | a result is requested from a `GO` analysis whose output does not exist yet (`NOT_STARTED`, `PLANNED`, `PROCESSING`, or recorded `FAILED`) |
| `SCIENTIFIC_PROCESSING_UNAVAILABLE` | 503 | the processing / artifact back end cannot be reached |
| `INTERNAL_PROCESSING_FAILURE` | 500 | unexpected server fault (never used for a *recorded* `FAILED` analysis, which is data, not a fault) |

The code→status pairing is schema-enforced. `message` is user-safe: no stack traces, paths or credentials (schema-enforced). **An error never carries scientific fields, and an unavailable result is never replaced by invented data.**

## 5. API specification (read-only, planned — not implemented)

**Common behavior**

- JSON UTF-8. Every response carries header `X-ISTMOSAR-Contract-Version: 1.0.0-rc.1`.
- **Collections** return one envelope everywhere: `{ "contract_version", "items": [...], "page": {"limit", "offset", "total"} }` (`api-responses.schema.json`). **Single resources** return the bare object. No endpoint returns a bare array.
- Pagination: `limit` (default 50, 1–200), `offset` (default 0). `page.total` counts records matching the filters before paging. Order is deterministic (stated per endpoint).
- **Empty results** are `200` with `items: []` and `total: 0`, never `404`. `404` means the *named resource* does not exist.
- Errors use `error.schema.json`.

| # | Endpoint | Purpose | Path / query parameters | Success response | Errors | Empty / paging | Frontend use |
|---|---|---|---|---|---|---|---|
| 1 | `GET /health` | process availability and contract version only (not science readiness) | none | `HealthResponse` `{status:"ok", contract_version}` | 500 | n/a | startup check; show contract-mismatch warning |
| 2 | `GET /api/study-areas` | list areas | `selection_status`, `country` (ISO alpha-2), `limit`, `offset` | `StudyAreaList` | 422 | `items: []`; ordered by `id` | area selector; candidate vs approved styling (FR-03) |
| 3 | `GET /api/scenes` | list catalog scenes | `area_id` (scenes whose footprint intersects the area box), `catalog_status`, `limit`, `offset` | `SceneList` | 404 unknown `area_id`; 422 | `items: []`; ordered by `acquisition_start_utc`, then `id` | scene selector, provenance panel (FR-01) |
| 4 | `GET /api/scenes/{id}` | one scene | path `id` | `Scene` (bare) | 404; 422 | n/a | provenance panel, limitations |
| 5 | `GET /api/scenes/{id}/layers` | **added by this review**: Level 1 radar layers of a scene | path `id`; query `role`, `limit`, `offset` | `LayerList` | 404; 422 | `items: []` when nothing extracted | Level 1 map layer (FR-02) |
| 6 | `GET /api/analyses` | list analyses, **including `NO_GO`, `INSUFFICIENT_EVIDENCE`, `PENDING`** | `area_id`, `scene_ids` (`a,b`), `compatibility_decision`, `lifecycle_status`, `limit`, `offset` | `AnalysisList` | 404 unknown `area_id`; 422; 422 `INVALID_SCENE_PAIR` | `items: []`; ordered by `id` | pair browser, blocked-state messages (FR-04) |
| 7 | `GET /api/analyses/{id}` | one analysis with decision, statistics, provenance | path `id` | `Analysis` (bare) | 404; 422 | n/a | decision panel, statistics (FR-07, FR-09) |
| 8 | `GET /api/analyses/{id}/layers` | output layers | path `id`; query `role`, `limit`, `offset` | `LayerList` | 404; 422; **role-filter errors below** | `items: []` is the normal state for `NO_GO` | before/after/change toggles (FR-06) |

**Why endpoint 5 exists.** Level 1 displays one scene without any analysis, and the seven conceptual routes had no way to serve its layer. The added route is symmetrical to endpoint 8. José may remove it if Level 1 layers are instead embedded elsewhere; that would be a contract change (§13).

**`role` filter semantics (endpoints 5 and 8).** Without `role`, the endpoint lists whatever layer records exist (possibly none) and returns `200`. With `role` set to a scientific output role (`BEFORE`, `AFTER`, `CHANGE`, `CHANGE_MASK`, `VALID_MASK`) and **no `AVAILABLE` layer of that role**, the API explains *why* instead of returning an ambiguous empty list:

| Analysis state | Response |
|---|---|
| decision `NO_GO` | `409 INCOMPATIBLE_OBSERVATIONS` (`detail` carries `compatibility_decision`, `reason_codes` = failed check ids) |
| decision `PENDING` or `INSUFFICIENT_EVIDENCE` | `409 UNVERIFIED_DATA` |
| decision `GO`, output not produced | `409 LAYER_NOT_GENERATED` |
| back end unreachable | `503 SCIENTIFIC_PROCESSING_UNAVAILABLE` |

The same error body is used by whatever backend resource serves a layer's `delivery` URL when its artifact is missing.

## 6. Layer delivery to Leaflet

A scientific GeoTIFF/COG is **not** something Leaflet can draw. The contract therefore separates:

- `raster` — the scientific artifact (GeoTIFF/COG, native CRS such as the UTM zone read from the HDF5 `projection` dataset, true grid spacing, nodata policy). Offered for download/analysis only.
- `delivery` — what the browser consumes. Allowed methods: `IMAGE_OVERLAY` (a PNG/WebP already **reprojected to EPSG:3857**, with `image_bounds_lonlat`, for `L.imageOverlay`), `XYZ_TILES` (a template with `{z}`, `{x}`, `{y}`, `tile_size`, `min_zoom`, `max_zoom`, tiles in EPSG:3857, pre-rendered or produced by a COG-aware tile service), or `NONE`.
- **GeoTIFF/COG is never a valid `delivery.method`** (schema-enforced; mutation test NEG-11). A client-side COG renderer would be a future, explicit contract change.
- Overlay bounds must equal the raster bounds (BR-04). Display colour ranges live in `legend`, never in the raster's units.
- Layer URLs are server-provided and never assembled in the browser from scene file names. `source_url` is a catalog link, not an access token.

## 7. Scientific rules and enforcement

**Method (Level 2 pairwise backscatter comparison):** for finite, positive **linear power** `P` on the same aligned, masked grid: `B_dB = 10 × log10(P)`; `Delta_dB = B_later_dB − B_earlier_dB`. GCOV products use gamma-naught by default; sigma-naught requires the product's conversion factor and must not be mixed with gamma-naught without a documented conversion. Both scenes use the same channel (e.g. `HHHH` on frequency A), the same convention and the same grid.

Who enforces what — **a passing JSON Schema is never proof of scientific correctness**:

| Rule | Enforced by |
|---|---|
| Shape, types, enums, ranges, UTC timestamps, https-only URLs, complete granule ID, no stray fields (so no secrets) | **JSON Schema** |
| NO_GO / INSUFFICIENT_EVIDENCE / PENDING expose no layers, no computed statistics, no method, no change claim; `COMPLETED` needs computed results; approval gates | **JSON Schema** (conditional rules) |
| Missing statistics are `null`, never `0`; no flood claim level exists | **JSON Schema** |
| BR-01 references resolve (area, scenes, layers, provenance, parent) | `validate_contracts.py` |
| BR-02 simulated and real records never reference each other | `validate_contracts.py` |
| BR-03 scene fields agree with the granule file name (cycle, track, frame, direction, mode, times, CRID, coverage), catalog URL, file name, maturity | `validate_contracts.py` |
| BR-04 west<east, south<north, closed polygon rings, Panama plausibility (catches swapped lat/lon), layer inside study area, overlay bounds = raster bounds | `validate_contracts.py` |
| BR-05 end ≥ start; same cycle+track = same pass; interval and earlier/later order agree with the times | `validate_contracts.py` |
| BR-06 all 12 checks present once; decision, evidence level and approval consistent with the checks; objective checks agree with scene metadata | `validate_contracts.py` |
| BR-07 selected channel is nominal and, once processing is claimed, verified in both HDF5 files | `validate_contracts.py` |
| BR-08 valid + invalid = total; changed ≤ valid; percentage matches; total = grid width×height; area not from degrees; area matches pixel area on an equal-area grid | `validate_contracts.py` |
| BR-09 gamma/sigma convention, channel and parameters agree across analysis, layers and provenance | `validate_contracts.py` |
| BR-10 provenance sources/outputs/CRS agree with scenes and layers | `validate_contracts.py` |
| BR-11 no credential-like keys or text; no local paths in any string | `validate_contracts.py` |
| BR-12 layer availability/quality consistent with its analysis | `validate_contracts.py` |
| BR-13 simulated records use `example.invalid` and `.simulated.` file names | `validate_contracts.py` |
| BR-14 a non-GO analysis owns no layers | `validate_contracts.py` |
| BR-15 copies embedded in API fixtures equal their source fixtures | `validate_contracts.py` |
| Catalog facts (MD5, times, footprint, track, frame, version) equal the live NASA record | `validate_contracts.py --verify-catalog` (online, optional) |
| Real valid-pixel overlap, real grid alignment, HDF5 channels truly present, product known issues, orbit/geolocation accuracy, seasonal context, any interpretation as surface water | **Human scientific review** (MH-05, MH-06, MH-07, MH-08); not automatable here |
| Raster availability reflects real artifact existence | **Future backend** (the contract only states the requirement) |

## 8. Example fixtures

Registered in `contracts/fixtures-manifest.json`; the validator fails if a file is unregistered.

| Fixture | Category | Shows |
|---|---|---|
| `study-area-candidate.json` | PROPOSED_STRUCTURE | candidate Chagres/Gatún box (not approved) |
| `study-area-gulf-of-parita-candidate.json` | PROPOSED_STRUCTURE | candidate Gulf of Parita box |
| `scene-d084.catalog.json` | VERIFIED_METADATA | authentic D084 CMR record; no raster extracted |
| `scene-d085.catalog.json` | VERIFIED_METADATA | authentic D085 CMR record; a scene without an extracted radar layer; partial frame |
| `analysis-d084-d085-NO-GO.json` | VERIFIED_METADATA | NO_GO temporal-pair decision; statistics `UNAVAILABLE`; no layers |
| `api-scenes-list.json`, `api-health.json`, `api-layers-list-empty.json` | PROPOSED_STRUCTURE | envelope, health, empty-result behavior |
| `error-incompatible-observations.json`, `error-resource-not-found.json` | PROPOSED_STRUCTURE | a failed layer request; an unknown id |
| `study-area-sim-training-box…`, `scene-sim-earlier/later…`, `analysis-sim-go-completed…`, `analysis-sim-insufficient-evidence…`, `layer-sim-before/after/change…` | SIMULATED_DATA | optional fields: statistics, provenance, both delivery methods, GO + COMPLETED + IN_REVIEW, INSUFFICIENT_EVIDENCE. Placed near 0°N 0°E, dated year 2000, with `example.invalid` URLs so they can never be mistaken for Panama or for NISAR data. |

Real facts in the fixtures are copied from the official CMR UMM-JSON records (EV-CMR-001, EV-CMR-002), including microsecond timestamps, product version `1.0.11`, CRID `P05023`, orbit 6367 and the MD5 declared by CMR. The D084 fixture's MD5 in the October 25 draft did not match the CMR record and was corrected; see the review report.

## 9. Validation

```text
pip install -r contracts/requirements.txt
python validate_contracts.py              # offline; exit 0 pass, 1 fail, 2 environment error
python validate_contracts.py -v           # list every passing check
python validate_contracts.py --verify-catalog   # ONLINE: compare verified scenes with live CMR
```

The validator loads and meta-validates every schema, resolves every `$ref` locally (no network), fails on missing format-checker packages (otherwise `date-time` and `uri` would be silently ignored), validates every fixture, runs BR-01…BR-15 across the fixture set, applies **50 declared mutation cases** (30 must be rejected by schema, 18 by business rules, 2 must remain valid) and checks manifest integrity. Mutations are declared as JSON patches in the manifest so reviewers can read what each negative test breaks. Run it from the repository root on Windows, macOS or Linux; it reads JSON with a BOM-tolerant decoder and prints ASCII only.

## 10. Consistency with neighbouring tasks

| Task | How this contract fits |
|---|---|
| **JP-05** Stage 0 consolidation | No approved record, decision or assignment is altered. Evidence IDs (`EV-CMR-001/002`, `EV-COL-001`) and `DEC-005` are referenced, not rewritten. |
| **JP-07** MVP acceptance tests | Each test area has a contract anchor and a fixture/test: official scene metadata → `scene` + BR-03 + `--verify-catalog`; coordinate correctness → BR-04, NEG-07…09, BIZ-07…09; pair compatibility → `compatibility.checks`, BR-05/06, NO-GO fixture, BIZ-10…12; raster/layer availability → `layer.availability`, BR-12/14, NEG-11…14; statistics → `statistics`, BR-08, NEG-23/25, BIZ-15/16; provenance → `provenance`, BR-10/11, NEG-20/26; API correctness → `api-responses` + API fixtures; error behavior → `error` + error fixtures, NEG-29/30. This is not an application test framework. |
| **JP-08** Environment | Only `jsonschema[format-nongpl]>=4.18,<5` on Python 3.10+ is required (`contracts/requirements.txt`). Future-stack packages (FastAPI, rasterio, h5py, …) are named in `docs/System-Architecture.md` and are intentionally **not** installed or pinned here. Conventions: UTF-8 without BOM, run from repo root, no credentials or HDF5 files in Git. |
| **JP-09** Compliance | See §0. Nothing here deploys or integrates a competition application. |

## 11. Frontend behavior rules (Level 1 / Level 2)

- The scene selector uses `scene.id`. The provenance panel shows the full `granule_id`, CMR link, acquisition time, product maturity, nominal vs verified channels and `limitations`.
- Show before/after/change toggles only for layers with `availability = AVAILABLE`. Label layers whose `quality_status` is not `PASSED` as **unreviewed**; never present a `COMPLETED` but non-`APPROVED` analysis as validated science.
- A `NO_GO`, `INSUFFICIENT_EVIDENCE` or `PENDING` analysis is shown as a research outcome with its failed or unevaluated checks, never as an empty map. Render `null` statistics as **Not calculated**.
- Candidate study areas are visually distinct from `APPROVED` ones. `SIMULATED_DATA` content carries a persistent "Simulated – not satellite data" badge.
- Convert `[west, south, east, north]` to Leaflet `[[south, west], [north, east]]` in one shared utility.
- Charts show only computed numbers with their units and provenance. Radar change is described as **radar backscatter change**, never as flooded area.

## 12. Migration from the October 25 draft (v1.0 → 1.0.0-rc.1)

| Draft | Now | Reason |
|---|---|---|
| single `analysis.status` (mixed lifecycle + decision) | `compatibility.decision` + `lifecycle_status` + `approval.status` | separate axes |
| `pair_assessment.decision` without `INSUFFICIENT_EVIDENCE`; free-text reasons | `compatibility.checks[12]` with machine-readable ids | auditable decisions |
| lower-case enums | `UPPER_SNAKE_CASE` | one convention |
| `analysis.layers[]` embedded | `layer_ids[]` + `/layers` | no duplicated payloads |
| `channel`, `method` including `"unselected"` and redundant `pairwise_log_ratio` | `selected_channel` / `processing_method` objects or `null` | null instead of sentinel; log-ratio equals ΔdB |
| `scientific_claim_level` with water-change values | `CATALOG_ONLY`, `RADAR_BACKSCATTER_CHANGE` | Level 3 is out of scope |
| layer `url`, `format` (incl. `geotiff`, `png_overlay`, `tile_xyz`), `units`, `measurement`, `status`, `nodata_policy` | `raster` + `delivery` + `measurement` + `availability` + `quality_status` | scientific artifact vs browser representation |
| scene `polarizations_nominal` / `polarizations_verified` (HH/HV names) | `frequencies[].polarizations_nominal` / `covariance_terms_verified` (HHHH names) | per-frequency, real dataset names |
| scene `md5`, `file_size_bytes` | `file.catalog_checksum`, `file.size_bytes` | declared vs verified checksum |
| scene `raster_status` | `extraction_status` + `quality_review` | two different questions |
| statistics `pixel_area_method` (`projected_equal_area`, `geodesic`) | `area_method` (`EQUAL_AREA_GRID`, `GEODESIC_PER_PIXEL`, `UTM_PLANIMETRIC_APPROX`, `NOT_CALCULATED`) + `area_crs` | honest area accounting |
| provenance flat fields | structured `sources`, `processing`, `outputs`, `review` | reproducibility |
| bare-array list responses | envelope with `page` | one convention; room for pagination |

## 13. Ownership, change control and sign-off

| Item | Accountable | Review |
|---|---|---|
| Scene catalog fields and scientific metadata | Maryfer | José |
| Pair criteria, QA masks, numeric units and thresholds | Maryfer | José + Tomás if available |
| API objects, response formats and version control | José | Maryfer |
| UI visibility and accessibility/testability | José | Xavier |
| Sensor endpoint (future extension only) | Xavier | José; not a Level 2 dependency |

**Change control:** any change to a schema, enum or API behavior requires a version bump, a reviewer, a recorded decision, a dated changelog line and matching fixture/mutation updates. `1.0.0-rc.1` → `1.0.0` happens only at José's sign-off.

## 14. Acceptance checklist for JP-06

- [x] Seven required contracts plus `common` and `api-responses` support schemas defined (Draft 2020-12, `$id`-addressed, no broken or circular references).
- [x] Read-only API documented with parameters, responses, errors, empty-result and pagination behavior.
- [x] Fixtures are structurally validated; rejected example carries no invented science.
- [x] 50 mutation tests pass; scientific business rules are separated from structural validation.
- [x] Statuses separated (decision / lifecycle / approval); categories VERIFIED_METADATA, PROPOSED_STRUCTURE, SIMULATED_DATA, UNAVAILABLE kept distinct.
- [ ] `python validate_contracts.py --verify-catalog` run once on a networked machine.
- [ ] Maryfer reviews scientific semantics (checks, units, area method); Xavier reviews UI assumptions; José signs off and bumps to `1.0.0`.
- [ ] José decides whether to keep the added `GET /api/scenes/{id}/layers` route.
- [ ] JP-09 outcome recorded before any implementation.
- [ ] Documents committed to GitHub (no claim of deployment).
