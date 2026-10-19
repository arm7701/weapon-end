# Phase 4 — Wing Database

ตารางและ API สำหรับข้อมูลกองบิน ตาม desktop (`0007`–`0014` รวมเป็น schema ปัจจุบัน)

## ตารางที่เพิ่ม

| ตาราง | หน้าที่ |
| --- | --- |
| `air_wings` | กองบิน + พิกัดบนแผนที่ |
| `wing_flying_units` | หน่วยบินภายใต้กองบิน |
| `wing_aircraft` | อากาศยาน (ผูก wing / flying unit) |
| `wing_pilots` | นักบิน + CEP / callsign |
| `wing_depots` | คลังของกองบิน |
| `wing_products` | สินค้า / อาวุธ (น้ำหนัก + unit cost) |
| `wing_depot_inventory` | สต็อกคลัง (unique depot+product) |
| `wing_depot_transfers` | ประวัติการโอนระหว่างคลัง |
| `wing_logistics_vehicles` | ยานพาหนะสนับสนุน |

หมายเหตุ: `DELETE` จะ **archive** (`status=archived`) ตามพฤติกรรม desktop ไม่ hard-delete

## Migration

```bash
cd weaponeering-backend
PYTHONPATH=src alembic -c alembic.ini upgrade head
```

หรือ restart container (entrypoint รัน migrate ให้)

## API (Bearer token)

| Method | Path | คำอธิบาย |
| --- | --- | --- |
| GET/POST | `/api/wings` | รายการ / สร้างกองบิน |
| GET | `/api/wings/summaries?scenario_id=` | สรุปจำนวนหน่วย/อากาศยาน/นักบิน/คลัง |
| GET | `/api/wings/{id}/map-detail?scenario_id=` | รายละเอียดสำหรับแผงแผนที่ |
| PATCH/DELETE | `/api/wings/{id}` | แก้ / archive |
| GET/POST | `/api/flying-units` | หน่วยบิน |
| PATCH/DELETE | `/api/flying-units/{id}` | |
| GET/POST | `/api/aircraft` | อากาศยาน |
| PATCH/DELETE | `/api/aircraft/{id}` | |
| GET/POST | `/api/pilots` | นักบิน |
| PATCH/DELETE | `/api/pilots/{id}` | |
| GET/POST | `/api/wing-depots` | คลังกองบิน |
| PATCH/DELETE | `/api/wing-depots/{id}` | |
| GET/POST | `/api/wing-products` | สินค้า |
| PATCH/DELETE | `/api/wing-products/{id}` | |
| GET | `/api/wing-depot-inventory` | สต็อก |
| GET | `/api/wing-depot-inventory/details?scenario_id=` | สต็อกพร้อมชื่อคลัง/สินค้า |
| PUT | `/api/wing-depot-inventory` | upsert สต็อก |
| DELETE | `/api/wing-depot-inventory/{id}` | archive สต็อก |
| POST | `/api/wing-depot-transfers` | โอนระหว่างคลัง |
| GET | `/api/wing-depot-transfers?scenario_id=` | ประวัติโอน |
| GET/POST | `/api/wing-vehicles` | ยานพาหนะ |
| PATCH/DELETE | `/api/wing-vehicles/{id}` | |

ตัวอย่างสร้างกองบิน + หน่วยบิน:

```bash
curl -X POST http://127.0.0.1:8000/api/wings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "'$SCENARIO_ID'",
    "wing_name": "กองบิน 1",
    "map_lat": 14.87,
    "map_lng": 100.65
  }'

curl -X POST http://127.0.0.1:8000/api/flying-units \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "'$SCENARIO_ID'",
    "wing_id": "'$WING_ID'",
    "unit_name": "ฝูงบิน 102"
  }'
```
