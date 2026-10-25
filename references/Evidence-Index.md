# ISTMOSAR — Evidence Index

**Updated:** October 25, 2026  
**Purpose:** Locate research, authentic source records, approvals and outstanding verification. An indexed item is not automatically a reviewed scientific product.

## A. Official catalog observations

| Evidence ID | Type | Source / locator | What it establishes | Status |
|---|---|---|---|---|
| EV-CMR-001 | NASA CMR UMM JSON | https://cmr.earthdata.nasa.gov/search/concepts/G4371433684-ASF.umm_json | Authentic D084 product metadata and footprint | INDEPENDENTLY CHECKED |
| EV-CMR-002 | NASA CMR UMM JSON | https://cmr.earthdata.nasa.gov/search/concepts/G4371282627-ASF.umm_json | Authentic D085 product metadata and footprint | INDEPENDENTLY CHECKED |
| EV-CMR-003 | NASA CMR UMM JSON | https://cmr.earthdata.nasa.gov/search/concepts/G4364362137-ASF.umm_json | Distinct-date search candidate; suitability not established | LEAD ONLY |
| EV-COL-001 | Official GCOV collection | https://cmr.earthdata.nasa.gov/search/concepts/C2854338529-ASF.umm_json | NISAR GCOV PROVISIONAL collection-level metadata | REFERENCE |

**Previously saved on José's Windows laptop; not necessarily in GitHub:**
`C:\Users\josep\Downloads\Space Dogs\ARPIP\ISTMOSAR\MH-01\evidence\G4371433684-ASF-official.json`
`C:\Users\josep\Downloads\Space Dogs\ARPIP\ISTMOSAR\MH-01\evidence\G4371282627-ASF-official.json`

To make the evidence versioned in the repository, copy the official public JSON files to `research/nisar/evidence/` after confirming their contents; record retrieval date and checksums. This package does **not** contain those JSON files.

## B. Submitted task evidence

| Evidence ID | Owner/task | Source artifact | Review outcome | Repository status |
|---|---|---|---|---|
| EV-JP-001 | José / JP-01 | `docs/MVP-Requirements.md` | APPROVED — planning | Existing document |
| EV-JP-002 | José / JP-02 | `docs/System-Architecture.md` | APPROVED — conceptual architecture | Existing document |
| EV-JP-003 | José / JP-03 | `docs/Backlog-and-Integration.md`, `team/Report-Template.md` | APPROVED — workflow | Existing documents |
| EV-JP-004 | José / JP-04 | `docs/Challenge-Rules.md` | APPROVED — provisional compliance research | Existing document; JP-09 open |
| EV-MH-001 | Maryfer / MH-01 | `ISTMOSAR_Panama_NISAR_GCOV_Final_Report.docx` + EV-CMR-001/002 | APPROVED — candidate inventory | Source DOCX not included in this package |
| EV-MH-002 | Maryfer / MH-02 | `MH-02_NISAR_GCOV_Metadata_Comparison_Panama.docx` | APPROVED — technical metadata | Source DOCX not included |
| EV-MH-003 | Maryfer / MH-03 | `MH-03_NISAR_GCOV_HDF5_Geographic_Processing_Notes.docx` | APPROVED — processing research | Source DOCX not included |
| EV-MH-004 | Maryfer / MH-04 | `MH-04_NISAR_GCOV_Comparable_Observations_Feasibility.docx` | APPROVED — evidence-based NO-GO on D084+D085 | Source DOCX not included |
| EV-XG-001 | Xavier / XG-01–XG-04 | Four-section report supplied to José on October 25: sensor comparison, ESP32 BOM, Wokwi feasibility, HTTP/FastAPI architecture | APPROVED — Stage 0 research | Save the original submission in `research/instrumentation/` and add its actual path here |
| EV-TS-001 | Tomás / TS-01–TS-04 | Not supplied/approved as of this review | OUTSTANDING | No accepted evidence indexed |

**Integrity notice:** Exact file names in the source-artifact column are historical document names. Do not create fake source reports or claim the files exist in GitHub without committing them or linking an accessible copy.

## C. Authoritative methodological references

| Evidence ID | Source | Use |
|---|---|---|
| EV-REF-001 | https://nisar-docs.asf.alaska.edu/ | NISAR data guide |
| EV-REF-002 | https://nisar-docs.asf.alaska.edu/gcov/ | GCOV format and processing context |
| EV-REF-003 | https://nisar-docs.asf.alaska.edu/provisional-known-issues/ | Product maturity and QA caveats |
| EV-REF-004 | https://nisar-docs.asf.alaska.edu/harmony/ | Extraction options (verify actual availability) |
| EV-REF-005 | https://asfopensarlab.github.io/NISAR_Cookbook/ | Training and change-detection recipes |
| EV-REF-006 | https://www.spaceappschallenge.org/2026/ | Event and submission information; verify current rules |
| EV-REF-007 | https://www.spaceappschallenge.org/legal/ | Official legal terms, eligibility and reuse policy |

## D. Evidence gaps requiring follow-up

- [ ] Link original Xavier report as actual repository file or approved shared-file URL.
- [ ] Link original Maryfer reports or safely publish a reviewed Markdown summary for each.
- [ ] Copy or securely archive two original CMR JSON payloads and record their SHA-256 checksums.
- [ ] Verify complete footprint and channel/geometry metadata for `G4364362137-ASF`.
- [ ] Identify a compatible different-date temporal pair or record a new defensible NO-GO.
- [ ] Confirm preparation and pre-existing-code reuse rules (JP-09).
- [ ] Add GitHub Issues/PR links to each new approved assignment as reviews occur.

**Caution:** Do not push personal credentials, SIM details, account information, large HDF5 scientific scenes, or private team data into the public repository.
