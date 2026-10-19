# Weaponeering Web API (FastAPI)

โค้ด desktop ต้นฉบับอยู่ใน `src/maap_app/` **เก็บไว้ครบ** เพื่อให้ AI/นักพัฒนาอ้างอิง logic เดิมได้

API ใหม่สำหรับ website อยู่ใน `src/weaponeering_api/`

Database เชื่อมผ่าน **pgpool** บน Docker network `shared-postgres-network` (รูปแบบเดียวกับ service-complaint)

Phase 0 รายละเอียด: [PHASE_0.md](PHASE_0.md)  
Phase 2 Targets: [PHASE_2_TARGETS.md](PHASE_2_TARGETS.md)  
Phase 3 Assets / Logistics: [PHASE_3_LOGISTICS.md](PHASE_3_LOGISTICS.md)  
Phase 4 Wing Database: [PHASE_4_WING.md](PHASE_4_WING.md)  
Phase 5 Weaponeering / Ranking: [PHASE_5_WEAPONEERING.md](PHASE_5_WEAPONEERING.md)  
Phase 6 Detection / Map extras: [PHASE_6_DETECTION.md](PHASE_6_DETECTION.md)

## Docker (แนะนำ)

จาก root ของ repo `weaponeering`:

```bash
# สร้าง network ถ้ายังไม่มี (ใช้ร่วมกับ pgpool บนเครื่อง)
docker network create shared-postgres-network

# ตั้งค่า env
cp weaponeering-backend/env.dev.example weaponeering-backend/.env
cp weaponeering-frontend/.env.example weaponeering-frontend/.env
cp .env.example .env

# แก้ DB_* ใน weaponeering-backend/.env ให้ตรงกับ pgpool

# Development (hot reload)
docker compose -f docker-compose.dev.yml up --build

# Production
docker compose -f docker-compose.yml up --build -d
```

- Frontend: http://localhost:3000
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## รัน API บนเครื่อง (ไม่ใช้ Docker)

```bash
cd weaponeering-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-api.txt

cp env.dev.example .env
# ถ้าอยู่บน host อาจต้องเปลี่ยน DB_HOST เป็น IP/host ของ pgpool ที่ expose ออกมา

PYTHONPATH=src uvicorn weaponeering_api.main:app --reload --port 8000
```

## Login (RTAF MFA)

`POST /api/mfa/login`

```json
{
  "user": "ukit_wu",
  "pass": "999804"
}
```

Backend จะเรียก `https://apigw.rtaf.mi.th/login-rtaf-mfa/v2/mfa/login` แล้วส่งต่อข้อมูลผู้ใช้ + `token` เมื่อสำเร็จ

## โครงสร้าง

```
weaponeering/
  docker-compose.yml
  docker-compose.dev.yml
  compose.yaml
  weaponeering-backend/
    Dockerfile / Dockerfile.dev
    entrypoint.sh / entrypoint-dev.sh
    env.dev.example / env.prod.example
    src/maap_app/           # desktop ต้นฉบับ (อย่าลบ)
    src/weaponeering_api/   # FastAPI + pgpool
  weaponeering-frontend/
    Dockerfile / Dockerfile.dev
    devops/nginx/default.conf
```
