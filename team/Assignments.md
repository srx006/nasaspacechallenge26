# ISTMOSAR — Team Assignment Register

**Project:** ISTMOSAR — Guardian of the Isthmus  
**Department:** Space Dogs — ARPIP  
**Technical Director:** José Peñalba  
**Register updated:** 2026-10-25  
**Review scope:** Original Stage 0 tasks and new preparation assignments (October 25–November 13, 2026)

## Status definitions

- **APPROVED:** Original research/planning deliverable accepted. This does not certify application implementation.
- **OUTSTANDING / DEFERRED:** Not submitted or not approved; no claim of completion.
- **PLANNED:** New assignment, not yet evidenced as finished.
- **BLOCKED:** External technical dependency remains unresolved, regardless of earlier research approvals.

## Stage 0 — historical register (due October 21, 2026)

| ID | Owner | Original deliverable (abbreviated) | Status | Decision / boundary |
|---|---|---|---|---|
| JP-01 | José Peñalba | MVP scope, required/optional features | APPROVED | Planning requirements, not software implementation |
| JP-02 | José Peñalba | Conceptual NISAR → Python → FastAPI → React architecture | APPROVED | Conceptual architecture only |
| JP-03 | José Peñalba | GitHub planning structure, tracking and templates | APPROVED | Repository planning package |
| JP-04 | José Peñalba | Event rules and reuse/compliance summary | APPROVED | Summary explicitly provisional; unresolved organizer questions remain for JP-09 |
| MH-01 | Maryfer Higuera | Candidate NISAR GCOV inventory | APPROVED | Two official NASA CMR candidates verified; inventory not exhaustive |
| MH-02 | Maryfer Higuera | Scene acquisition and technical metadata comparison | APPROVED | Granule-level metadata verified; not HDF5 science-pixel QA |
| MH-03 | Maryfer Higuera | HDF5/GCOV geographic-processing technical notes | APPROVED | Research notes only; no claim extraction has run |
| MH-04 | Maryfer Higuera | Evidence-based compatible-pair GO/NO-GO | APPROVED | D084+D085: NO-GO for before/after; other pairs unresolved |
| XG-01 | Xavier Guevara | Rain/humidity/water-level sensor comparison | APPROVED | Research and scientific applicability |
| XG-02 | Xavier Guevara | ESP32 preliminary BOM and compatibility/costs | APPROVED | Estimates, not verified quotes or checked physical inventory |
| XG-03 | Xavier Guevara | Wokwi simulation OR feasibility/limitations documentation | APPROVED | Documentation option fulfilled; no running simulation claimed |
| XG-04 | Xavier Guevara | Sensor → Wi-Fi → FastAPI telemetry design | APPROVED | Conceptual data path, no live integration claimed |
| TS-01 | Tomás Strandgard | Three detailed historical SAR project studies | OUTSTANDING / DEFERRED | Not approved as of this review |
| TS-02 | Tomás Strandgard | Six additional historical project summaries | OUTSTANDING / DEFERRED | Not approved as of this review |
| TS-03 | Tomás Strandgard | Competitive comparison matrix | OUTSTANDING / RESCOPED | Replaced prospectively by TS-06 |
| TS-04 | Tomás Strandgard | Scientific verification checklist | OUTSTANDING / RESCOPED | Replaced prospectively by TS-05 |

**Stage 0 summary:** 12 approved original tasks / 16 assigned. Four Tomás tasks remain unapproved. Stage 0 research approval is distinct from Level 1/Level 2 MVP readiness.

## Stage 1 — revised preparation assignments

**Scope:** research, planning, standalone training and test design. Competition-solution implementation begins only when authorized under event rules. New task IDs do not retroactively complete the original tasks.

| ID | Owner | Deliverable | Target | Status | Priority |
|---|---|---|---|---|---|
| JP-05 | José | Updated assignments, review decisions, evidence index committed to repository | Oct 26 | IN PROGRESS (package prepared; commit pending) | P0 |
| JP-06 | José | API/frontend data contract: scene, analysis, layers, statistics, provenance JSON structures | Oct 29 | PLANNED | P0 |
| JP-07 | José | L1/L2 acceptance test plan: provenance, alignment, reproducibility | Nov 1 | PLANNED | P0 |
| JP-08 | José | Tool checklist, repo conventions, event task board | Nov 5 | PLANNED | P0 |
| JP-09 | José | Reuse/preparation compliance decision or organizer clarification | Before implementation | PLANNED | P0 |
| MH-05 | Maryfer | Different-date observation search overlapping D084 / Chagres-Gatún, catalog log | Oct 27 | PLANNED | P0 |
| MH-06 | Maryfer | Alternative pair comparison + GO/NO-GO and fallback recommendation | Oct 29 | PLANNED | P0 |
| MH-07 | Maryfer | GCOV HDF5 → geographic-layer processing runbook | Nov 1 | PLANNED | P0 |
| MH-08 | Maryfer | Level 2 scientific QC/reproducibility checklist | Nov 3 | PLANNED | P0 |
| XG-05 | Xavier | Inventory actually available hardware; distinguish verified/unidentified parts | Oct 27 | PLANNED | P2 |
| XG-06 | Xavier | Standalone Wokwi/ESP32 learning exercise, example measurements and evidence | Oct 30 | PLANNED | P2 |
| XG-07 | Xavier | Future telemetry JSON with timestamps, units, status/error semantics | Nov 1 | PLANNED | P2 |
| XG-08 | Xavier | Browser/mobile and demonstration test checklist | Nov 5 | PLANNED | P1 |
| TS-05 | Tomás | Minimum scientific claims QA checklist (1 page) | Oct 29 | PLANNED | P1 |
| TS-06 | Tomás | Concise three-project competitor comparison (1 page) | Nov 2 | PLANNED | P2 |
| TS-07 | Tomás | Narrative/scientific-claims review comments | Nov 7 | PLANNED | P1 |

**Fallback:** If TS-05 is not supplied October 29, José prepares the minimum claims checklist, with Maryfer reviewing scientific accuracy; mark reassignment and actual completion separately.

## Active scientific dependency

- **BLOCKED — Level 2 compatible temporal pair:** the two official granules already independently verified (D084 and D085) are adjacent frames acquired on October 14, 2026, not a suitable two-date pair. Search for independent different-date overlapping observations remains open. See `docs/Stage-0-Decisions.md` and `references/Evidence-Index.md`.
- **NOT COMPLETE:** No genuine GCOV science raster extraction, pixel QA, or integrated React/FastAPI MVP is represented as finished by this register.

## Review and change control

For every completed new task, link its report or issue, evidence, reviewer, decision date and limitations. Do not change PLANNED to APPROVED without verifying the deliverable. Store secrets, credentials, and large raw satellite HDF5s outside ordinary Git commits.
