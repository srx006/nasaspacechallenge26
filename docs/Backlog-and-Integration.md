# Backlog and Integration Plan

## Stage gates
G0 evidence: verified NISAR records; G1 level 1 radar exploration; G2 level 2 change visualization and complete demo (MVP); G3 supported open-water interpretation; G4 assessed wetland classification; G5 independent enhancements. Advance to an optional module only after maintaining working G2 release.

## Prioritized backlog
P0: verified source records and AOI; manifest; UI scene metadata; one GCOV layer; compatible pair; masks/alignments; reproducible change raster; map controls; interpretation/limitations; end-to-end demo and fallback.
P1: supported open-water map, validated area statistics, contextual reference evidence, wetland HH/HV comparison if quality allows.
P2: second vegetation module using same GCOV infrastructure.
P3: separate GUNW earthquake module, only if pair and coherence validated.
P4: SME2/agriculture and ESP32, chatbot/Ollama, multiple regions, advanced model after stable core.

## Ownership and interfaces
Maryfer: scene inventory/verification, channel and QA method; produces approved scene manifest and scientific validation note.
José: backlog, architecture, API contract, integration, core frontend/backend coordination and demo.
Tomás: scientific claims checklist, sources, user testing, documentation and presentation, phone-friendly.
Xavier: conditional ESP32 research, sensor relevance, technical evaluation; supports interface and demonstrator checks.

## Hackathon progression (subject to rules)
Start: create project skeleton and confirm datasets / status.
Build L1: one scene visualized with source panel.
Build L2: pair comparison, change layer and documentation.
Freeze working main branch and capture repeatable demo.
Only then: L3 water interpretation, L4 wetland science, second project, optional features.

## Demo sequence
1. State question and geography; 2. show NASA provenance; 3. show first observation; 4. show second comparable observation; 5. enable difference layer; 6. explain visible change and numerical summary; 7. show quality and uncertainty; 8. connect result to Panama and indicate future modules. Never call a backscatter mask a confirmed flood map without validation.
