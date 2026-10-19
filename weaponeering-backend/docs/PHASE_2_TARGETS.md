# Phase 2 — Targets

ตารางและ API สำหรับเป้าหมาย ตาม desktop (`target_cards` + โปรไฟล์ + พิกัด + recognition + review)

## ตารางที่เพิ่ม

| ตาราง | หน้าที่ |
| --- | --- |
| `target_cards` | บัตรเป้าหมาย + โปรไฟล์ (type, CEP, PK, ฯลฯ) |
| `target_coordinates` | พิกัดหลายจุดของเป้า |
| `target_recognition_results` | ผลการรู้จำ / บันทึก recognition |
| `human_review_records` | บันทึกการ review |

อัปเดต `map_nodes`: `linked_entity_type`, `linked_entity_id`, `is_synthetic_location`

## Migration

```bash
cd weaponeering-backend
PYTHONPATH=src alembic -c alembic.ini upgrade head
```

หรือ restart container (entrypoint รัน migrate ให้)

## API (Bearer token)

| Method | Path | คำอธิบาย |
| --- | --- | --- |
| GET | `/api/targets?scenario_id=` | รายการเป้า |
| POST | `/api/targets` | สร้างเป้า (+ พิกัด / recognition ได้) |
| GET | `/api/targets/{id}` | รายละเอียด |
| PATCH | `/api/targets/{id}` | แก้ไข |
| DELETE | `/api/targets/{id}` | ลบ |
| POST | `/api/targets/{id}/recognitions` | เพิ่ม recognition |
| POST | `/api/reviews` | สร้าง human review |

ตัวอย่างสร้างเป้า:

```bash
curl -X POST http://127.0.0.1:8000/api/targets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "'$SCENARIO_ID'",
    "label": "อาคารเป้าหมาย A",
    "target_type": "BUILDING",
    "priority_score": 4,
    "cep": 10,
    "coordinates": [
      {"label": "จุดหลัก", "map_lat": 13.75, "map_lng": 100.50, "is_primary": true}
    ]
  }'
```
