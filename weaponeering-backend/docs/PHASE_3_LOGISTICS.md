# Phase 3 — Assets / Logistics

ตารางและ API สำหรับหน่วย / แพลตฟอร์ม / คลัง / เส้นทาง ตาม desktop (`0003_phase_3_assets_logistics.sql`)

## ตารางที่เพิ่ม

| ตาราง | หน้าที่ |
| --- | --- |
| `organizations` | หน่วย / องค์กรใน scenario |
| `platform_types` | ประเภทแพลตฟอร์ม (capability / cost) |
| `simulated_platforms` | แพลตฟอร์มจำลองที่ผูกกับหน่วย |
| `platform_readiness_events` | ประวัติ readiness ของแพลตฟอร์ม |
| `depots` | คลัง / จุดเก็บทรัพยากร |
| `resource_tokens` | token ทรัพยากรระดับ scenario |
| `depot_inventory` | สต็อกในคลัง |
| `transport_assets` | ยานพาหนะ / สินทรัพย์ขนส่ง |
| `route_segments` | เส้นทางระหว่าง entity |
| `plan_scores` | คะแนน feasibility ของแผน (soft-ref `plan_option_id`) |

## Migration

```bash
cd weaponeering-backend
PYTHONPATH=src alembic -c alembic.ini upgrade head
```

หรือ restart container (entrypoint รัน migrate ให้)

## API (Bearer token)

กรองด้วย `?scenario_id=` ได้เกือบทุก list endpoint

| Method | Path | คำอธิบาย |
| --- | --- | --- |
| GET/POST | `/api/organizations` | รายการ / สร้างหน่วย |
| GET/PATCH/DELETE | `/api/organizations/{id}` | ดู / แก้ / ลบ |
| GET/POST | `/api/platform-types` | ประเภทแพลตฟอร์ม |
| GET/PATCH/DELETE | `/api/platform-types/{id}` | |
| GET/POST | `/api/platforms` | แพลตฟอร์มจำลอง |
| GET/PATCH/DELETE | `/api/platforms/{id}` | |
| POST | `/api/platforms/{id}/readiness` | บันทึก readiness + อัปเดตสถานะ |
| GET/POST | `/api/depots` | คลัง |
| GET/PATCH/DELETE | `/api/depots/{id}` | |
| GET/POST | `/api/resource-tokens` | resource tokens |
| GET/PATCH/DELETE | `/api/resource-tokens/{id}` | |
| GET/POST | `/api/depot-inventory` | สต็อกคลัง (`?depot_id=`) |
| PATCH/DELETE | `/api/depot-inventory/{id}` | |
| GET/POST | `/api/transport-assets` | สินทรัพย์ขนส่ง |
| GET/PATCH/DELETE | `/api/transport-assets/{id}` | |
| GET/POST | `/api/route-segments` | เส้นทาง |
| GET/PATCH/DELETE | `/api/route-segments/{id}` | |
| GET/POST | `/api/plan-scores` | คะแนนแผน |
| DELETE | `/api/plan-scores/{id}` | |

ตัวอย่างสร้างหน่วย + คลัง:

```bash
curl -X POST http://127.0.0.1:8000/api/organizations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "'$SCENARIO_ID'",
    "name": "กองบิน 1",
    "organization_type": "wing",
    "map_lat": 14.87,
    "map_lng": 100.65
  }'

curl -X POST http://127.0.0.1:8000/api/depots \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "'$SCENARIO_ID'",
    "name": "คลังสนับสนุน A",
    "capacity_score": 70
  }'
```

หมายเหตุ: `plan_scores.plan_option_id` เป็น soft reference — ตาราง `plan_options` จะมาใน Phase Weaponeering
