# Phase 0 — Database foundation (PostgreSQL / pgpool)

## ตารางที่สร้าง

| ตาราง | หน้าที่ |
| --- | --- |
| `users` | โปรไฟล์จาก RTAF MFA |
| `auth_sessions` | เก็บ token หลัง login |
| `app_settings` | ค่าคอนฟิกระบบ |
| `scenarios` | สถานการณ์ฝึก (ฐานของ Phase 1+) |
| `learning_objectives` | วัตถุประสงค์การเรียนรู้ |
| `map_nodes` | จุดบนแผนที่ใน scenario |
| `audit_events` | บันทึกการกระทำ |
| `guardrail_events` | บันทึก guardrail |

## Migration

```bash
cd weaponeering-backend
PYTHONPATH=src alembic -c alembic.ini upgrade head
```

ใน Docker จะรันอัตโนมัติตอน start (`entrypoint*.sh`)

## API

ต้องส่ง `Authorization: Bearer <token>` (token จาก `/api/mfa/login`)

| Method | Path | คำอธิบาย |
| --- | --- | --- |
| POST | `/api/mfa/login` | login + บันทึก user/session |
| GET | `/api/me` | โปรไฟล์ผู้ใช้ปัจจุบัน |
| GET | `/api/scenarios` | รายการ scenario |
| POST | `/api/scenarios` | สร้าง scenario |
| GET | `/api/scenarios/{id}` | รายละเอียด |
| PATCH | `/api/scenarios/{id}` | แก้ไข |
| DELETE | `/api/scenarios/{id}` | ลบ |
| GET | `/api/audit-events` | ดู audit log |
| GET | `/health` | สุขภาพระบบ + สถานะ DB |

ตัวอย่างสร้าง scenario:

```bash
curl -X POST http://127.0.0.1:8000/api/scenarios \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Scenario ฝึก 1",
    "description": "ทดสอบ Phase 0",
    "map_nodes": [
      {"label": "จุด A", "map_lat": 13.75, "map_lng": 100.5}
    ]
  }'
```
