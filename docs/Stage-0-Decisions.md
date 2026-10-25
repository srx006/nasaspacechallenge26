# ISTMOSAR — Stage 0 Review and Decision Log

**Decision log version:** 1.0  
**Prepared:** 2026-10-25  
**Technical director:** José Peñalba  
**Original Stage 0 due date:** October 21, 2026  
**Basis:** Submitted research, technical directive, repository planning package and separately performed CMR checks.

## Decisions

| ID | Decision | Supporting evidence | Limitation / carryover |
|---|---|---|---|
| DEC-001 | ACCEPT JP-01–JP-04 as Stage 0 planning deliverables | `docs/MVP-Requirements.md`, `docs/System-Architecture.md`, `docs/Backlog-and-Integration.md`, `docs/Challenge-Rules.md`, and team templates | Prepared documentation is not implemented software; event-specific reuse terms still require JP-09 |
| DEC-002 | ACCEPT MH-01 candidate inventory | Official NASA CMR UMM metadata for D084 and D085, verified independently | Two candidates, not exhaustive catalog coverage |
| DEC-003 | ACCEPT MH-02 metadata research | `MH-02_NISAR_GCOV_Metadata_Comparison_Panama.docx` | Derived from official catalog metadata, not QA of full HDF5 measurements |
| DEC-004 | ACCEPT MH-03 processing-method research | `MH-03_NISAR_GCOV_HDF5_Geographic_Processing_Notes.docx` | Documented methods, extraction not executed |
| DEC-005 | ACCEPT MH-04 GO/NO-GO research | `MH-04_NISAR_GCOV_Comparable_Observations_Feasibility.docx` | NO-GO for D084+D085 before/after; feasibility of an alternate pair unresolved |
| DEC-006 | ACCEPT XG-01–XG-04 Stage 0 research | Xavier's four-part submitted report: sensors, preliminary ESP32 BOM, Wokwi feasibility, proposed telemetry JSON | No actual Wokwi execution, vendor-verified prices, or physical sensor system claimed |
| DEC-007 | KEEP TS-01–TS-04 outstanding | No accepted submissions reported by project technical director | TS-01/02 deferred; TS-03/04 prospectively rescoped into TS-06/TS-05 |
| DEC-008 | RETAIN Level 1+Level 2 as protected MVP | Official Technical Development Directive v1.0 | L2 cannot pass without a compatible real NISAR pair and reproducible processing |
| DEC-009 | MOVE optional ESP32 into independent support stream | Directive's Level 5 optionality; Xavier's completed feasibility research | Sensor demonstration is not a prerequisite for radar change MVP |
| DEC-010 | OPEN Stage 1 preparation task register | `team/Assignments.md` | New assignments are PLANNED until evidence is submitted |

## Verified observation facts

| Property | D084 | D085 |
|---|---|---|
| NASA CMR concept ID | `G4371433684-ASF` | `G4371282627-ASF` |
| UTC acquisition start | `2026-10-14T23:44:44Z` | `2026-10-14T23:45:16Z` |
| Relative track / direction | `040 / descending` | `040 / descending` |
| Frame | `084` | `085` |
| Mode / nominal channels | `4005 / DHDH (HH/HV)` | `4005 / DHDH (HH/HV)` |
| Product collection | `NISAR_L2_GCOV_PROVISIONAL_V1` | `NISAR_L2_GCOV_PROVISIONAL_V1` |
| Granule coverage flag | `F` (full) | `P` (partial) |
| File size, bytes | `4,991,221,760` | `2,571,108,352` |
| CMR UMM record | https://cmr.earthdata.nasa.gov/search/concepts/G4371433684-ASF.umm_json | https://cmr.earthdata.nasa.gov/search/concepts/G4371282627-ASF.umm_json |

**Interpretation:** D084 and D085 are authentic, but not a valid temporal before/after pair. Their spatial coverage and nearly simultaneous acquisition do not prove environmental change. D084 is the initial Chagres/Gatún candidate; D085 primarily supports further coverage investigation in the Gulf of Parita.

**Unresolved search lead (not approved):** `G4364362137-ASF`, acquisition October 12, 2026, ascending track 004. Its complete footprint, geographic overlap and geometric comparability must be verified. Do not list this as a usable pair.

## MVP acceptance status

| Gate | Status | Reason |
|---|---|---|
| Stage 0 documentary scope and architecture | APPROVED | JP documentation accepted as planning |
| Authentic candidate metadata inventory | APPROVED | At least two official CMR records confirmed |
| Compatible two-date pair | BLOCKED / UNRESOLVED | D084+D085 fails temporal requirement; alternative unverified |
| Authentic extracted and georeferenced GCOV raster | NOT DEMONSTRATED | Extraction and raster QA not performed in accepted Stage 0 research |
| Level 1 radar application | NOT IMPLEMENTED | Existing GitHub package contains planning documents |
| Level 2 integrated change application | NOT IMPLEMENTED | Requires valid pair, processing, visualization and reproducibility |
| Optional telemetry / ESP32 integration | DEFERRED | Research approved but physical build not required |

## Next decision gates

1. **DATA-G1:** Maryfer provides official CMR identifiers for two different-date, overlapping candidate granules.
2. **DATA-G2:** Pair geometry, polarizations, measurement convention, maturity, quality and valid-pixel overlap reviewed.
3. **PROC-G1:** Georeferenced output extraction procedure scientifically validated when permitted and feasible.
4. **APP-G1/G2:** Actual application development, demonstrations and acceptance occur within competition authorization.
5. **COMPLIANCE-G1:** José documents governing rules and any organizer clarification on pre-event development and reuse.

**Review note:** The approved MH-04 NO-GO conclusion is an accepted research result, not a failed assignment. This log replaces outdated statements in older directive sections suggesting the verified October 2026 CMR records were still absent; preserve original documents as historical records rather than silently rewriting them.
