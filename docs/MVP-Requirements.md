# ISTMOSAR — MVP Requirements v1.0
Owner: José Peñalba | Space Dogs — ARPIP | 2026-10-19 | Status: PROVISIONAL

## Challenge alignment
Interactive application using authentic NASA–ISRO NISAR radar observations to track and visualize surface change. Focus on Panama when data permit; no unverified scenes are accepted.

## Product objective
Enable a user to inspect two compatible, verified NISAR L2 GCOV observations of one area, inspect a reproducible georeferenced radar backscatter change map, and understand the metadata, measurement, and scientific limitations. First scientific module: Panama Surface Water Change Observatory. Interpret water only when independent evidence supports it.

## Functional requirements and acceptance
| ID | Requirement | Acceptance test | Gate |
|---|---|---|---|
| FR-01 | Traceable authentic NISAR data | Full granule IDs, dates, collection, geometry, channels and catalog links shown | L1 |
| FR-02 | SAR raster explorer | Valid georeferenced layer displays over correct area | L1 |
| FR-03 | Study-area selection | One verified AOI is shown and documented | L1 |
| FR-04 | Pair validation | Two records with compatible product, channel, geometry, grid and overlap, with QC log | L2 |
| FR-05 | Repeatable change analysis | Documented code/method generates change raster from inputs with mask and consistent units | L2 |
| FR-06 | Interactive change visualization | Before/after/change layers and legend selectable in Leaflet | L2 |
| FR-07 | Scientific communication | Clearly distinguishes radar change from claimed flood or cause; limitations shown | L2 |
| FR-08 | Full demonstration | Local/deployed demo functions with packaged prepared outputs and a backup recording | L2 |
| FR-09 | Reproducibility | Provenance manifest, parameters, processing versions and outputs included | L2 |

## Optional science and product requirements
| Stage | Feature | Scientific gate |
|---|---|---|
| L3 | Candidate open-water change interpretation | Reference/context evidence and justified method |
| L4 | Wetland and inundated vegetation classes | Appropriate HH/HV and independent validation |
| L5 | ESP32, multiple areas, GIBS, chatbot, local model, advanced AI | Main MVP finished, tested, compliant and not degraded |

## Explicit exclusions for L2 MVP
Real-time flood warning, quantitative water-level inference from GCOV alone, flood prediction, automatic causal attribution, guaranteed classification accuracy, generic AI diagnosis, InSAR earthquake displacement, broad multi-country coverage, live ESP32 acquisition, processing a full HDF5 on every map request.

## Scientific handling requirements
Compare the same geophysical diagonal GCOV channel and compatible data maturity, calculate 10*log10(power) only on positive finite calibrated backscatter, create nodata/QA masks, align rasters to a defined grid, document resampling and threshold methods. A backscatter difference is not automatically water/flood/deformation.

## Data gate
Maryfer provides independently retrievable official catalog records and a comparison table. Search Panama first, including PROVISIONAL data since June 17 2026; do not assume failed earlier searches establish absence. If no viable pair: select alternative Panama AOI, then scientifically justified alternative international AOI, then consider a different NISAR product or challenge-compliant demonstration. Sentinel-1 methodology alone cannot substitute for the challenge's NISAR requirement.

## Definition of MVP complete
All L1 and L2 requirements pass on authentic eligible NISAR data, source citations are included, demo and offline fallback function, and team records reviewed approval. No other module or optional sensor/AI feature required.
