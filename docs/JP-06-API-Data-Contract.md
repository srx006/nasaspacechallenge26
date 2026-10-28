# ISTMOSAR — JP-06 API and Frontend Data Contract v1.0

**Owner:** José Peñalba · Space Dogs / ARPIP  
**Prepared:** October 25, 2026 · **Target review:** October 29, 2026  
**Status:** PROPOSED CONTRACT — planning specification; **not deployed API or implemented application**.  
**Source of alignment:** Existing `docs/MVP-Requirements.md`, `docs/System-Architecture.md`, `docs/Stage-0-Decisions.md`, and `references/Evidence-Index.md`.

## 1. Objective and boundaries

Freeze the **shape** of data passed from the future NASA/ASF scene catalog + Python processing pipeline through FastAPI to React/Leaflet/Chart.js. Schema files are design artifacts. No actual HDF5 files have been processed or validated by the examples. The two verified October 14 granules are **NOT** a scientifically usable temporal pair.

Level 1 needs study-area metadata, authentic scene provenance, and a QA-approved georeferenced radar layer. Level 2 additionally needs two distinct suitable acquisitions, documented alignment/quality masking, backscatter-change output, statistics and limitations. Environmental sensors are **out of scope** for this contract version.

## 2. API surface (proposed, read-only)

| Method | Path | Response | Notes |
|---|---|---|---|
| GET | `/health` | `{"status":"ok","api_contract":"v1"}` | Availability only; not science readiness. |
| GET | `/api/study-areas` | Array of study-area objects | Each matches `study-area.schema.json`. |
| GET | `/api/scenes?area_id=...` | Array of scene objects | Catalog candidates can exist before raster extraction. |
| GET | `/api/scenes/{id}` | One scene | 404 if missing. |
| GET | `/api/analyses?area_id=...` | Array of analysis records | Includes NO_GO and PENDING, not just completed. |
| GET | `/api/analyses/{id}` | Analysis object | `analysis.schema.json`. |
| GET | `/api/analyses/{id}/layers` | Array of layer objects | May be empty when blocked. |

Common behavior: JSON UTF-8; API error objects use `error.schema.json`; absent resources return HTTP 404; invalid parameters return 422; server faults return 500. Endpoint names align with the current architecture except for optional scene-detail path. Suggested future prefix `/api/v1` requires an explicit versioning decision (not silently introduced here).

## 3. Canonical record contracts

- **Study Area:** `id`, `name`, `region`, `bbox_lonlat` in `[west,south,east,north]`, approval `status`, optional Polygon geometry. A candidate AOI is not an approved scientific case.
- **Scene:** internal `id`; **full original** `granule_id`; `cmr_concept_id`; collection/product; start/end UTC; relative track, direction, frame; nominal versus verified polarizations; footprint GeoJSON Polygon `[longitude, latitude]` WGS84; official `source_url`; file size/checksum; catalog and raster states. *Catalog authenticity is not valid-pixel QA.*
- **Layer:** role `before/after/change/change_mask/valid_mask/context`; `status`, source scene IDs, URL nullable until generated, CRS, unit, measurement convention, nodata policy, bounds and legend. A GeoTIFF download URL is not automatically a browser-displayable map tile: a map service/COG-aware renderer or a georeferenced web overlay must be chosen during implementation.
- **Analysis:** exactly two scene IDs, pair compatibility decision, selected covariance channel, method, layer list, statistics, provenance, limitations and scientific-claim level. `NO_GO` pairs remain visible as **research outcomes**; they must never show invented change rasters.
- **Statistics:** valid pixels, changed pixels, percentage, mean ΔdB, changed area, area-computation method. Values `null` mean **not calculated**, never zero. All values must refer to the same QC-accepted comparison footprint.
- **Provenance:** exact source granule identifiers, science dataset paths inspected, processing state, versioned software, algorithm parameters, quality checks, processing time, optional output SHA-256 and scientific caveats.

## 4. Scientific rules (beyond basic JSON Schema)

1. Only process real science data after confirming HDF5 dataset presence, QA and interpretation of channel names, measurement convention and calibration. Granule filename `DHDH` is nominal; it does not prove which datasets have actually been extracted.
2. Confirm two acquisitions at scientifically appropriate distinct dates, spatial valid-pixel overlap, compatible viewing geometry, product maturity, polarization and same measurement convention. Catalog polygon overlap alone is insufficient.
3. Convert only positive finite **linear power** to dB as `10 * log10(power)`; compare identically defined channels on aligned grids with quality/nodata masks. Define difference as `later_dB - earlier_dB` and record resampling, CRS, grid spacing and threshold in provenance.
4. `changed_pixel_pct = 100 * changed_pixel_count / valid_pixel_count`, when `valid_pixel_count > 0`; `changed_area_km2` requires documented pixel area accounting. Never label this number as confirmed flooded area.
5. `pair_rejected` or `pair_pending` must not contain calculated radar-change statistics or QA-passed output layers. Null statistics signal absence of evidence.
6. `qa_passed` requires evidence of extracted real rasters, processing checks and a reproducibility record; basic JSON validation alone **does not** grant scientific approval.
7. API returns ISO 8601 UTC timestamps (for example `2026-10-14T23:44:44Z`), units in explicit standardized strings, and source granule names unmodified. Do not expose secrets, NASA account tokens or private SIM/device credentials.
8. Product maturity and source limitations must be shown in the UI. Radar backscatter difference is not, by itself, flood detection, depth measurement, vegetation loss or deformation.

## 5. React/Leaflet integration decisions

- Scene selector uses `scene.id`; provenance panel displays full `granule_id`, CMR link, timestamp, channels and status.
- Before/after/change toggles read `analysis.layers` **only when** `status == qa_passed` and individual layers are `qa_passed`.
- Show unavailable / blocked messages when a pair is `NO_GO` or pending. Render `null` statistics as **Not calculated**.
- Study areas in `candidate` state must be visually distinguished from `approved` cases.
- Map layer URLs are server-provided, never manufactured by concatenating untrusted scene filenames in the browser. No use of `source_url` as an access token.
- Charts display only calculated numeric metrics with correct units and provenance.

## 6. Example fixtures and limitations

- `contracts/examples/scene-d084.catalog.json`: **authentic CMR-derived metadata**; raster **not extracted**. Footprint coordinates are longitude then latitude and only represent catalog coverage.
- `contracts/examples/study-area-candidate.json`: proposed Chagres/Gatún AOI box, not scientifically approved.
- `contracts/examples/analysis-d084-d085-NO-GO.json`: truthful rejected temporal pair; layers empty; statistics null; no calculated result or fabricated flood claim.

## 7. Stage gate and ownership

| Item | Accountable | Review |
|---|---|---|
| Scene catalog fields and scientific metadata | Maryfer | José |
| Pair criteria, QA masks, numeric units and thresholds | Maryfer | José + Tomás if available |
| API objects, response formats and version control | José | Maryfer |
| UI visibility and accessibility/testability | José | Xavier |
| Sensor endpoint (future extension only) | Xavier | José; not a Level 2 dependency |

**Contract change control:** proposal updates require a version bump, reviewer, decision, dated changelog and corresponding fixture/schema update. Schema acceptance is a JP-06 planning milestone only; Level 1/2 science and application implementation remain pending.

## 8. Acceptance criteria for JP-06

- [ ] All six contracts (study-area, scene, layer, analysis, statistics, provenance) documented.
- [ ] Read-only API endpoints and error shape specified.
- [ ] Example source scene uses authentic catalog data; rejected example has no invented science results.
- [ ] JSON fixtures validate against supplied schemas.
- [ ] Distinct catalog/processing/pair statuses documented.
- [ ] Responsibilities and UI behavior clearly stated.
- [ ] Maryfer reviews scientific semantics; Xavier reviews UI assumptions; José signs off.
- [ ] Documents committed to GitHub (no claim of deployment).
