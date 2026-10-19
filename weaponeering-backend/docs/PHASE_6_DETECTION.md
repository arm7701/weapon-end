# Phase 6 — Detection / Map extras

ตารางและ API สำหรับผล detection บนแผนที่, team markers และ ground transport

## ตารางที่เพิ่ม

| ตาราง | หน้าที่ |
| --- | --- |
| `target_map_detection_runs` | ผล detection ต่อเป้า + พิกัด (unique target×coordinate) |
| `target_map_detection_objects` | วัตถุที่ตรวจพบ (polygon, risk, confidence) |
| `scenario_team_markers` | marker ฝ่าย blue/red บนแผนที่ (+ unit_type, radius) |
| `scenario_ground_transports` | การขนส่งภาคพื้นระหว่างกองบิน (+ route geometry) |

## Migration

```bash
cd weaponeering-backend
PYTHONPATH=src alembic -c alembic.ini upgrade head
```

## API (Bearer token)

### Detection

| Method | Path | คำอธิบาย |
| --- | --- | --- |
| GET | `/api/detection-runs?scenario_id=&target_card_id=` | รายการ runs |
| GET | `/api/detection-runs/by-coordinate?target_card_id=&target_coordinate_id=` | run ตามพิกัด |
| GET | `/api/detection-runs/{id}` | รายละเอียด + objects |
| PUT | `/api/detection-runs` | upsert run + objects |
| DELETE | `/api/detection-runs/{id}` | ลบ run |
| GET | `/api/detection-map-objects?scenario_id=` | objects รวมสำหรับชั้นแผนที่ |

### Team markers

| Method | Path | คำอธิบาย |
| --- | --- | --- |
| GET/POST | `/api/team-markers` | รายการ / สร้าง |
| PATCH/DELETE | `/api/team-markers/{id}` | แก้ / ลบ |

`side`: `blue` \| `red`  
`unit_type`: `generic` \| `radar` \| `tank` \| `small_arms` \| `artillery` \| `anti_air`

### Ground transports

| Method | Path | คำอธิบาย |
| --- | --- | --- |
| GET/POST | `/api/ground-transports` | รายการ / สร้าง |
| PATCH/DELETE | `/api/ground-transports/{id}` | แก้ / archive |

ตัวอย่าง upsert detection:

```bash
curl -X PUT http://127.0.0.1:8000/api/detection-runs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "'$SCENARIO_ID'",
    "target_card_id": "'$TARGET_ID'",
    "target_coordinate_id": "'$COORD_ID'",
    "model_name": "yolov8n",
    "radius_m": 500,
    "capture_radius_m": 600,
    "objects": [
      {
        "map_object_id": "obj-1",
        "object_label": "radar",
        "object_type": "radar",
        "risk_level": "high",
        "confidence": 0.92,
        "center_lat": 14.87,
        "center_lng": 100.65,
        "polygon_json": [[14.87, 100.65], [14.871, 100.651]]
      }
    ]
  }'
```

หมายเหตุ: logic คำนวณ risk direction / corridor route จาก desktop อยู่ใน `maap_app/modules/detection/`

### Detection inference (YOLO)

| Method | Path | คำอธิบาย |
| --- | --- | --- |
| GET | `/api/detection-models` | รายการโมเดล + ค่าเริ่มต้น radius/zoom |
| POST | `/api/detection-runs/execute` | อัปโหลดภาพจับจากแผนที่ → YOLO (`building-seg.pt`) → upsert + คำนวณทางเข้า/ออก |
| GET | `/api/detection-runs/risk-direction?target_card_id=&target_coordinate_id=` | คำนวณทิศทางเสี่ยงต่ำ / เข้า-ออก จากผล detection ที่มีอยู่ |

`POST /detection-runs/execute` เป็น `multipart/form-data`:
- `scenario_id`, `target_card_id`, `target_coordinate_id`
- `model_name` (default `Building Detector`)
- `radius_m`, `zoom_level`
- `image` (PNG จตุรัสจาก Cesium viewport)

ติดตั้ง dependency เพิ่ม: `pip install -r requirements-detection.txt`  
วางน้ำหนักที่ `weaponeering-backend/building-seg.pt` (dev compose mount แล้ว)

`GET /api/map/layers` จะแนบ `lowestRiskDirection` ให้ target ที่มี detection แล้ว (ลูกศรแนะนำ + border entry/exit)
