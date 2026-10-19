# MAAP Wargame Training Simulation

เอกสารชุดนี้เป็น blueprint สำหรับพัฒนา **Master Air Attack Plan (MAAP) Wargame / Training Simulation Desktop System** ที่ทำงานแบบ local-only บนเครื่อง desktop และใช้ข้อมูลจำลองเท่านั้น

ระบบนี้ออกแบบมาเพื่อช่วยฝึกการวิเคราะห์, การจัดลำดับความสำคัญ, การทบทวนแผน, และการอธิบายเหตุผลของแผนแบบ MAAP-style โดยไม่ใช่ระบบปฏิบัติการจริง ไม่ใช่ระบบ targeting จริง และไม่ใช่ระบบ weaponeering จริง

## Concept

ระบบทำงานบนแนวคิด map-first desktop workspace:

- ด้านบนเป็นเมนู workflow เช่น Map, Target, Database, AI Review, AAR & Export, Settings
- ด้านซ้ายเป็นข้อมูลเป้าหมายปัจจุบัน เช่น Target Cards, Target Recognition, review status
- ตรงกลางเป็นแผนที่จำลองสำหรับแสดง targets, organizations, depots, route segments, readiness, logistics, ranking overlays
- ด้านขวาเป็นผลลัพธ์ AI/MAAP เช่น priority ranking, score breakdown, AI explanation, review actions, export readiness

## Core Workflow

1. สร้าง synthetic scenario และ learning objectives
2. เพิ่ม synthetic map nodes, organizations, depots, platforms, resource tokens, transport assets, route segments
3. ทำ Target Recognition จากข้อมูลจำลองและแปลงเป็น Target Cards
4. เชื่อม Target Cards กับ Abstract Weaponeering Options
5. ประเมิน readiness, depot availability, route friction, logistics feasibility
6. สร้าง Priority Ranking สำหรับ Target Cards และ plan options
7. ให้ AI ช่วยอธิบาย ranking, missing data, และ draft plan summary
8. ส่ง AI-generated content เข้า Human Review
9. Export เฉพาะข้อมูล simulation ที่ผ่าน review แล้ว

## Key Design Rules

- Local desktop only
- Synthetic training data only
- Abstract scoring only
- Human review required for AI-generated or imported sensitive content
- No real target nomination
- No real weapon selection
- No operational Weaponeering
- No real JMEM calculation inside this project
- No live intelligence, readiness, inventory, navigation, mission, or command integration

## Weaponeering Scope

ระบบรองรับเฉพาะ **Abstract Weaponeering Scoring**:

- ใช้คะแนนจำลอง เช่น `abstract_effect_score`, `option_suitability_score`, `option_feasibility_score`, `logistics_demand_score`, `risk_score`
- รองรับการ import ผลลัพธ์แบบ abstract จาก external Weaponeering result adapter
- เก็บผลไว้ในรูปแบบ training-safe scoring records
- ไม่เก็บสูตรจริง, real JMEM formulas, PK/PD, CEP/TLE/MAE, weapon names, munition quantities, aircraft/weapon pairing หรือ real effect calculations

ไฟล์ `doc/JMEM_AS_Program_Reference.md` เป็น reference แยกต่างหาก ไม่ใช่ design file หลักของระบบ และไม่ควรถูกนำไป implement เป็น operational calculation ภายใน project นี้

## Documentation

| File | Purpose |
| --- | --- |
| [WEB API](docs/WEB_API.md) | FastAPI + Docker + pgpool สำหรับ website — โค้ด desktop ต้นฉบับใน `src/maap_app` ถูกเก็บไว้ครบ |
| [00 Improved Prompt](doc/00_Improved_Prompt.md) | prompt หลักที่สรุปความต้องการทั้งหมดของระบบสำหรับให้ AI/developer ใช้ต่อ |
| [01 Requirements](doc/01_Requirements.md) | functional, non-functional, data, AI, guardrail, role และ acceptance requirements |
| [02 System Architecture](doc/02_System_Architecture.md) | architecture ของ desktop app, map-first UI, local services, data flow และ guardrail boundary |
| [03 Service Design](doc/03_Service_Design.md) | service boundaries, responsibilities, operations, database mapping, validation และ failure behavior |
| [04 Database Design](doc/04_Database_Design.md) | SQLite-oriented schema สำหรับ scenario, targets, assets, depots, routes, ranking, AI, review, guardrail, audit |
| [05 Workflow](doc/05_Workflow.md) | end-to-end workflow ตั้งแต่ scenario setup ถึง target recognition, ranking, AI review และ export |
| [06 AI Module Design](doc/06_AI_Module_Design.md) | AI task types, context bundles, prompt contract, output schemas, classifier, validator และ review integration |
| [07 Wargame Simulation](doc/07_Wargame_Simulation.md) | simulation state model, scoring model, ranking formula, map layers, injects, replay และ after-action review |
| [08 Desktop UI UX](doc/08_Desktop_UI_UX.md) | map-first desktop UI layout, top menu, left target panel, center map, right MAAP panel, states และ data binding |
| [09 Glossary](doc/09_Glossary.md) | คำศัพท์สำคัญของระบบเพื่อให้ทีมพัฒนาเข้าใจตรงกัน |
| [10 Development Phases](doc/10_Development_Phases.md) | แผนแบ่งเฟสการพัฒนา ตั้งแต่ foundation จนถึง export/replay/AAR |
| [11 Phase 1 Functional Requirements](doc/11_Phase_1_Functional_Requirements.md) | FR สำหรับเฟสแรก ครอบคลุม foundation, scenario core, map node, audit และ guardrail stub |
| [12 Phase 2 Functional Requirements](doc/12_Phase_2_Functional_Requirements.md) | FR สำหรับ Target Recognition Core, Target Cards, recognition results, left panel และ target-map sync |
| [13 Phase 3 Functional Requirements](doc/13_Phase_3_Functional_Requirements.md) | FR สำหรับ Assets, Depot, Logistics Base, readiness, route segments และ logistics feasibility |
| [14 Phase 4 Functional Requirements](doc/14_Phase_4_Functional_Requirements.md) | FR สำหรับ Abstract Weaponeering, external abstract import, scoring profiles และ Priority Ranking |
| [15 Phase 5 Functional Requirements](doc/15_Phase_5_Functional_Requirements.md) | FR สำหรับ AI Assistant, context bundles, classifier/validator, review queue และ human review actions |
| [16 Phase 6 Functional Requirements](doc/16_Phase_6_Functional_Requirements.md) | FR สำหรับ local export package, export manifest, ranking replay, ranking comparison, AAR summary และ AAR action items |
| [17 Technical Stack And Code Structure](doc/17_Technical_Stack_And_Code_Structure.md) | stack สำหรับ Python native desktop app, service-oriented modules, repository, schema, scoring function และ project structure |

## Main Domain Objects

- Scenario
- Learning Objective
- Target Card
- Target Recognition Result
- Map Node
- Organization
- Depot
- Depot Inventory
- Resource Token
- Platform Type
- Simulated Platform
- Platform Readiness Event
- Transport Asset
- Route Segment
- Abstract Weaponeering Option
- Target Weaponeering Assessment
- Scoring Profile
- Ranking Run
- Ranking Item
- Plan Option
- Plan Assignment
- Plan Score
- AI Interaction
- Human Review Record
- Guardrail Event
- Audit Event

## Main Services

- Scenario Service
- Target Recognition Service
- Organization And Asset Service
- Depot And Inventory Service
- Abstract Weaponeering Integration Service
- Logistics Feasibility Service
- Priority Ranking Service
- AI Assistant Service
- Human Review Service
- Export Service
- Audit Service
- Guardrail Service
- Settings Service

## Suggested Implementation Direction

- Language: Python
- Desktop UI: PySide6 / Qt native desktop application
- Application style: desktop app only, not a website
- Backend logic: Python service classes and pure functions
- Database access: repository classes over SQLite
- Database: SQLite
- Validation: Pydantic or dataclasses with explicit validation
- Map workspace: Leaflet embedded in Qt WebEngine for Phase 1 synthetic map; PMTiles/MBTiles can be considered later if storage allows
- UI model: persistent top menu, left Target Panel, center Synthetic Map, right MAAP AI Output Panel
- AI: local or explicitly sandboxed adapter, disabled/offline by default
- Scoring: deterministic, ruleset-versioned, abstract 1-100 scores
- Export: local files only, reviewed simulation content only

## Phase 1 Map Approach

Phase 1 uses a Leaflet map embedded in the Qt desktop shell.

- Leaflet assets are bundled locally under `src/maap_app/ui/map/assets/`.
- The base map uses Google Hybrid tiles (satellite imagery with road/place labels).
- Tile loading requires internet access.
- Map workspace includes a local YOLO Object Detection Layer control:
  `Detection` toggle, model selector, radius selector, and `Run Detection`.
- YOLO output is rendered as colored polygons/bounding boxes around the selected
  Target for simulation-only risk annotation.
- Install optional detection dependencies with `pip install -e ".[detection]"`.
- Put local YOLO weights in `~/.local/share/maap_wargame_simulation/models/`:
  `building-seg.pt`, `vehicle-det.pt`, or `structure-seg.pt`.
- `Run Detection` automatically focuses the map on the selected Target, captures
  a square viewport crop, saves it under
  `~/.local/share/maap_wargame_simulation/detection_sources/`, and sends it to
  YOLO.
- The captured map viewport uses a Cesium rectangle derived from meters around
  the selected Target, scans a wider context than the selected radius, then
  filters YOLO objects back to the selected radius for risk annotation. Use
  `Source Image` only when you want to override the automatic viewport capture
  with your own local image.

### Train Custom YOLO Detection Model

For building/structure detection from satellite imagery, train a custom model
instead of using a generic YOLO model.

1. Export your Roboflow dataset as a YOLO segmentation/detection dataset with a
   `data.yaml` file.
2. Install detection dependencies:

```bash
pip install -e ".[detection]"
```

3. Train and install the model into the desktop app:

```bash
python scripts/train_yolo_model.py \
  --data /path/to/roboflow-dataset/data.yaml \
  --base yolo11n-seg.pt \
  --target building \
  --epochs 80 \
  --imgsz 1024 \
  --batch 4
```

The script copies `best.pt` to:

```text
~/.local/share/maap_wargame_simulation/models/building-seg.pt
```

Then select `Building Detector` in the Map workspace and run detection.

## AI Settings

Open the `Settings` tab to configure AI:

- `rule_based`: offline deterministic helper.
- `local_model`: local LLM server with an Ollama-compatible `/api/chat` endpoint.
- `openai`: OpenAI-compatible chat completions endpoint with API key.
- `disabled`: AI calls are disabled.

Example local LLM endpoint:

```bash
curl -X POST http://10.222.22.222:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.1:8b","messages":[{"role":"user","content":"สวัสดี"}],"stream":false}'
```

AI settings are stored locally in the app data folder.
Use `Test Connection` to send a small training-safe test request to the selected adapter before saving or using it in workflow.

## Phase 2 Target Recognition

Phase 2 adds a functional left Target Panel:

- Target Card CRUD with guardrail validation and audit events.
- Target Recognition Result CRUD (summary, confidence, missing-data notes).
- Search and filters (category, review status).
- Link Target Card to a synthetic map node via **Link to Map**.
- Map marker click syncs back to the selected Target Card.
- SQLite tables: `target_cards`, `target_recognition_results`, `human_review_records`.

## Phase 3 Assets & Logistics

Phase 3 adds synthetic support data and logistics scoring:

- Organization, Platform Type, Simulated Platform CRUD with readiness events.
- Depot, Resource Token, Depot Inventory, Transport Asset CRUD.
- Route Segment CRUD with map polylines.
- Map layers: Organization (blue), Depot (green), Route (yellow) with toggles.
- **Calculate Logistics Feasibility** — abstract 1–100 score stored in `plan_scores`.
- Assets & Logistics tab in the left panel; score shown in the right MAAP panel.

## Phase 4 Weaponeering & Ranking

Phase 4 adds abstract weaponeering and Priority Ranking Engine v1:

- Abstract Weaponeering Option CRUD with training-only effect categories.
- Target Weaponeering Assessment CRUD linked to Target Cards.
- JSON/CSV import with `weaponeering_import_batches` and guardrail rejection.
- Scoring Profile CRUD with weighted ranking formula.
- Ranking Run + Ranking Items with score breakdown stored in `breakdown_json`.
- Right MAAP panel ranking table, breakdown, instructor override, and draft plan options.
- **Weaponeering & Ranking** tab in the left panel with **Run Ranking**.

## Phase 5 AI Assistant & Human Review

Phase 5 adds a local AI assistant and human review workflow:

- Rule-based local AI adapter (disabled / rule_based / local_model / sandboxed modes).
- Sanitized context bundles, input classifier, and output validator.
- AI tasks: target summary, missing-data explanation, ranking explanation, draft plan summary, instructor questions.
- `ai_interactions` storage with guardrail-backed validation.
- **AI Review** tab with approve, reject, and request revision actions.
- AI Review supports normal chat against the selected Target or scenario-wide context.
- Chat memory is built from recent local `ai_interactions` for the selected Target/scenario and sent with the next LLM request.
- AI Review shows Target-filtered chat-room bubbles with dialogs for raw LLM input/output inspection.
- Right MAAP panel AI output section with explain ranking and review controls.
- Left Target panel **AI Summarize** and **AI Missing Data** buttons.

## Phase 6 Export, Replay & AAR

Phase 6 completes the training workflow with local artifacts:

- Export readiness checks with guardrail and review gate validation.
- Export types: scenario brief, targets, weaponeering, logistics, ranking, scorecard, instructor notes, audit, full package, AAR.
- Formats: Markdown, CSV, JSON (with manifest for full package).
- Ranking run comparison and deterministic replay with difference explanation.
- AAR summary generation and action items (`aar_action_items`).
- **AAR & Export** tab; export readiness shown in right MAAP panel.

## Run The Desktop App

Create and use a local virtual environment first:

```bash
cd /Users/ukitwuthpornpong/Projects/RTAF/AI/master-air-attack-plan
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m maap_app
```

Run tests:

```bash
cd /Users/ukitwuthpornpong/Projects/RTAF/AI/master-air-attack-plan
source .venv/bin/activate
PYTHONPATH=src python -m pytest -q
```

If you run `PYTHONPATH=src python3 -m maap_app` without installing dependencies first, Python may fail with `ModuleNotFoundError: No module named 'PySide6'`.

## Current Status

This repository now contains planning/design Markdown files and a complete Phase 1–6 Python/PySide6 desktop application.
