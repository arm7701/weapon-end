# Phase 5 — Weaponeering / Ranking

ตารางและ API สำหรับ abstract weaponeering options, target assessments, deployment plans, ranking และ plan options

## ตารางที่เพิ่ม

| ตาราง | หน้าที่ |
| --- | --- |
| `abstract_weaponeering_options` | ตัวเลือก weaponeering (effect, risk, logistics) |
| `target_weaponeering_assessments` | ประเมินความเหมาะสมของตัวเลือกกับเป้า |
| `weaponeering_import_batches` | ประวัตินำเข้าชุดข้อมูล |
| `target_weaponeering_deployment_plans` | แผนส่งกำลังต่อเป้า (unique target_card) |
| `target_weaponeering_deployment_aircraft` | สายอากาศยานในแผน |
| `target_weaponeering_deployment_waypoints` | waypoint เส้นทางบิน |
| `scoring_profiles` | โปรไฟล์น้ำหนักคะแนน |
| `ranking_runs` | ผลการจัดลำดับ (run) |
| `ranking_items` | รายการ entity ที่ถูกจัดลำดับ + override |
| `plan_options` | แผนเลือก (title + horizon) |
| `plan_assignments` | มอบหมายเป้า/แพลตฟอร์ม/คลังให้แผน |

## Migration

```bash
cd weaponeering-backend
PYTHONPATH=src alembic -c alembic.ini upgrade head
```

## API (Bearer token)

| Method | Path | คำอธิบาย |
| --- | --- | --- |
| GET/POST | `/api/weaponeering-options` | ตัวเลือก weaponeering |
| GET/PATCH/DELETE | `/api/weaponeering-options/{id}` | |
| GET/POST | `/api/weaponeering-assessments` | ประเมิน target×option |
| DELETE | `/api/weaponeering-assessments/{id}` | |
| GET/PUT/DELETE | `/api/deployment-plans/{target_card_id}` | แผนส่งกำลัง (upsert) |
| GET/POST | `/api/scoring-profiles` | โปรไฟล์คะแนน |
| PATCH/DELETE | `/api/scoring-profiles/{id}` | |
| GET/POST | `/api/ranking-runs` | สร้าง ranking run |
| GET/DELETE | `/api/ranking-runs/{id}` | รายละเอียด + items |
| PATCH | `/api/ranking-items/{id}/override` | override ลำดับ |
| GET/POST | `/api/plan-options` | แผนเลือก |
| PATCH/DELETE | `/api/plan-options/{id}` | |
| GET/POST | `/api/plan-assignments` | มอบหมาย |
| DELETE | `/api/plan-assignments/{id}` | |

ตัวอย่าง:

```bash
# สร้าง weaponeering option
curl -X POST http://127.0.0.1:8000/api/weaponeering-options \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "'$SCENARIO_ID'",
    "option_label": "Precision Strike - GBU-12",
    "effect_category": "abstract_disrupt",
    "estimated_effect_score": 80,
    "risk_score": 30
  }'

# upsert deployment plan
curl -X PUT http://127.0.0.1:8000/api/deployment-plans \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "'$SCENARIO_ID'",
    "target_card_id": "'$TARGET_ID'",
    "wing_id": "'$WING_ID'",
    "flying_unit_id": "'$FU_ID'",
    "aircraft_lines": [{"aircraft_id": "'$AC_ID'", "aircraft_count": 2}],
    "waypoints": [{"lat": 14.5, "lng": 100.3}]
  }'
```

หมายเหตุ: logic คำนวณ ranking score (weighted aggregate) จาก desktop อยู่ใน `maap_app/modules/ranking/scoring.py` — จะ implement endpoint สำหรับ "run" จริงใน phase ถัดไป (AI/Review) ที่จะเรียก scorer อัตโนมัติ
