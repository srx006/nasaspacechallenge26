# ISTMOSAR — Active Risks, Blockers and Mitigations

**Updated:** 2026-10-25

| ID | Type | Risk or blocker | Impact | Owner | Next action | Due / decision |
|---|---|---|---|---|---|---|
| BL-01 | SCIENTIFIC BLOCKER | No accepted compatible temporal NISAR GCOV pair for Level 2 | Stops defensible before/after result | Maryfer | MH-05/MH-06: catalog search and pair GO/NO-GO | Oct 27–29 |
| BL-02 | PROCESSING RISK | Authentic GCOV HDF5 → geographic layer pipeline not executed/QA-checked | Level 1 imagery not demonstrated | Maryfer, José | Prepare MH-07 runbook; later independently execute and check | Nov 1 plan |
| BL-03 | COMPLIANCE RISK | Authorized reuse and pre-event code/dataset boundaries not resolved | May invalidate submission practice | José | JP-09 official rule/organizer clarification | Before implementation |
| BL-04 | SCHEDULING RISK | Tomás's four original Stage 0 tasks outstanding | QA/documentation could slip | José, Tomás | Reduce to TS-05/06/07; fallback for TS-05 | Oct 29 |
| BL-05 | INTEGRATION RISK | Frontend/backend schema not yet frozen | Data handoff uncertainty | José | JP-06 data contract | Oct 29 |
| BL-06 | RESOURCE RISK | Multi-GB GCOV files and intermittent connectivity | Download/processing delays | José, Maryfer | Study spatial subsetting, lightweight test AOI and offline strategy | Before build |

**Policy:** No simulated sensor output may be labeled satellite data, and radar backscatter change alone is not proof of flooding.
