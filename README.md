# Weaponeering Decision Support System (RTAF)

ระบบวิเคราะห์และวางแผนการใช้อาวุธทางอากาศ (Weaponeering) สำหรับเว็บไซต์ (**Vue 3 + Vite + CesiumJS** และ **FastAPI + SQLAlchemy Async + PostgreSQL `pgpool`**) โดยคงโมดูลคำนวณหลักจากระบบ Desktop ต้นฉบับไว้ใน `weaponeering-backend/src/maap_app` พร้อมฐานข้อมูล `pgpool` ที่บรรจุข้อมูลคลังอาวุธ JMEM และเป้าหมายตัวอย่าง 3 มิติพร้อมใช้งานทันที

---

## 📁 โครงสร้างโปรเจกต์ (Project Structure)

```text
weaponeering/
├── compose.yaml                     # Docker Compose หลัก (เรียกใช้ docker-compose.dev.yml)
├── docker-compose.dev.yml           # Docker Compose สำหรับรันครบชุด (pgpool + Backend + Frontend Hot-Reload)
├── docker-compose.pgpool.yml        # Docker Compose สำหรับรันเฉพาะฐานข้อมูล pgpool (PostgreSQL 17 + ข้อมูลเริ่มต้น)
├── docker-compose.yml               # Docker Compose สำหรับ Production (pgpool + Backend + Frontend Nginx)
├── database/
│   └── init/
│       └── 01_weaponeering_dump.sql # ไฟล์ SQL Dump จาก pgpool ปัจจุบัน (Schema 0001–0012 + คลังอาวุธ JMEM + เป้าหมายตัวอย่าง 3D)
├── api-manual.md                    # คู่มือการเชื่อมต่อระบบ AI Assistant (RAG Platform API)
├── weaponeering-backend/            # FastAPI Backend + Alembic Migrations (0001–0012)
│   ├── alembic/versions/            # สคริปต์สร้างตารางฐานข้อมูลและ Seed คลังอาวุธมาตรฐาน
│   └── src/
│       ├── maap_app/                # โมดูลคำนวณหลัก (JMEM, Target Footprint 3D, Weapon Effects, Laser Designation, Circular Error)
│       └── weaponeering_api/        # REST API Routers, Services, SQLAlchemy Models, Schemas
└── weaponeering-frontend/           # Vue 3 + Vite Frontend + CesiumJS 3D Map
    ├── public/map/cesium_map.html   # แผนที่ปฏิบัติการ 3 มิติหลัก (CesiumJS Embed)
    └── src/
        ├── components/
        │   ├── MapPanel.vue         # คอนเทนเนอร์ควบคุมแผนที่หลัก ตรงกลาง
        │   ├── MapDetailSidebar.vue # แถบแสดงรายการเป้าหมาย, JMEM Advisor, Detection และทิศทางเข้าโจมตี
        │   ├── Sidebar.vue          # แถบซ้ายสำหรับกรอกข้อมูลเป้าหมาย (กว้าง×ยาว×สูง, ทิศ Heading, ความแข็งแรงวัสดุ)
        │   ├── RightPanel.vue       # แถบขวาแสดงผล Recommendation, AI Analysis, AI Chatbot (RAG API), Export รายงาน และ Mission Simulator
        │   └── SimulatorDemo.vue    # หน้าจอ 3D Mission Simulator (กล่อง 3D แสดงตลอด + ดูวงรัศมีทำลายล้างแต่ละเป้าหมาย)
        └── views/                   # หน้าจอหลัก (Analysis, Wing Data, Logistics, Reports, Login)
```

---

## 🚀 วิธีการติดตั้งและรันระบบ (Installation Guide)

สามารถเลือกติดตั้งได้ **2 วิธี** ตามความสะดวกของนักพัฒนา:
- **วิธีที่ 1**: รันฐานข้อมูล **`pgpool` บน Docker** แล้วรัน Backend / Frontend บนเครื่อง (แนะนำสำหรับการพัฒนาและแก้ไขโค้ด)
- **วิธีที่ 2**: รันทุกบริการ (`pgpool` + `weaponeering-backend` + `weaponeering-frontend`) ด้วยคำสั่ง `docker compose up` คำสั่งเดียว

---

### วิธีที่ 1: รัน `pgpool` บน Docker + รัน Backend & Frontend บนเครื่อง (แนะนำสำหรับ Dev)

#### ขั้นตอนที่ 1: เปิดใช้งานฐานข้อมูล `pgpool` ด้วย Docker
ในโฟลเดอร์หลักของโปรเจกต์ มีไฟล์ `docker-compose.pgpool.yml` และไฟล์ข้อมูล `database/init/01_weaponeering_dump.sql` ที่ดึงข้อมูลล่าสุดจาก `pgpool` มาให้เรียบร้อยแล้ว (เมื่อสร้าง Container ครั้งแรก PostgreSQL จะ Import ตารางทั้งหมด คลังอาวุธ JMEM และ Scenario เป้าหมายตัวอย่าง 3 มิติให้อัตโนมัติ):

```bash
# สั่งรัน Container pgpool (PostgreSQL พอร์ต 5432)
docker compose -f docker-compose.pgpool.yml up -d
```

> **กรณีต้องการ Restore ข้อมูลลง Container `pgpool` ที่มีอยู่เดิมด้วยตัวเอง:**
> ```bash
> docker exec -i pgpool psql -U postgres -d weaponeering < database/init/01_weaponeering_dump.sql
> ```

---

#### ขั้นตอนที่ 2: ติดตั้งและรัน Backend (FastAPI พอร์ต `8000`)
ต้องมี **Python 3.11+** ติดตั้งอยู่ในเครื่อง

```powershell
cd weaponeering-backend

# 1. ติดตั้งไลบรารีที่จำเป็น
pip install -e .

# 2. ตั้งค่า Environment Variables เชื่อมต่อกับ pgpool
# (สำหรับ PowerShell บน Windows)
$env:PYTHONPATH="src"
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="5432"
$env:DB_USER="postgres"
$env:DB_PASSWORD="postgres"
$env:DB_NAME="weaponeering"

# (สำหรับ macOS / Linux / Git Bash)
# export PYTHONPATH=src DB_HOST=127.0.0.1 DB_PORT=5432 DB_USER=postgres DB_PASSWORD=postgres DB_NAME=weaponeering

# 3. ตรวจสอบ/อัปเดต Alembic Migration ให้เป็นเวอร์ชันล่าสุด (0001–0012)
python -m alembic upgrade head

# 4. รันเซิร์ฟเวอร์ FastAPI ที่พอร์ต 8000
python -m uvicorn weaponeering_api.main:app --host 127.0.0.1 --port 8000 --reload
```

---

#### ขั้นตอนที่ 3: ติดตั้งและรัน Frontend (Vue 3 + Vite พอร์ต `5173`)
ต้องมี **Node.js 18+** ติดตั้งอยู่ในเครื่อง

```powershell
cd weaponeering-frontend

# 1. ติดตั้งแพ็กเกจทั้งหมด (รวมถึง CesiumJS และ MGRS parser)
npm install

# 2. รันเซิร์ฟเวอร์สำหรับพัฒนาที่พอร์ต 5173
npx vite --port 5173

# (ทางเลือก) ทดสอบสั่ง Build สำหรับ Production
npx vite build
```

---

### วิธีที่ 2: รันครบทุกส่วนด้วย Docker Compose (`pgpool` + `backend` + `frontend`)

```bash
# 1. คัดลอกไฟล์ .env ตัวอย่าง (หากยังไม่มี)
cp .env.example .env
cp weaponeering-backend/.env.example weaponeering-backend/.env
cp weaponeering-frontend/.env.example weaponeering-frontend/.env

# 2. สั่งรันทั้งระบบ (โหมด Development พร้อม Hot-Reload)
docker compose -f docker-compose.dev.yml up -d --build

# หรือรันโหมด Production (Nginx พอร์ต 3000)
docker compose -f docker-compose.yml up -d --build
```

---

## 🌐 ตารางพอร์ตและ URL สำหรับเข้าใช้งาน

| บริการ (Service) | URL (รันบนเครื่อง Dev) | URL (รันผ่าน Docker Compose) | รายละเอียด |
| --- | --- | --- | --- |
| **Frontend Web UI** | `http://localhost:5173` | `http://localhost:3000` | หน้าเว็บหลักของระบบ Weaponeering |
| **Backend API** | `http://127.0.0.1:8000` | `http://localhost:8000` | FastAPI REST Server |
| **Swagger API Docs** | `http://127.0.0.1:8000/docs` | `http://localhost:8000/docs` | เอกสารทดสอบ API ทั้งหมด |
| **PostgreSQL (`pgpool`)** | `localhost:5432` | `pgpool:5432` | User: `postgres` / Pass: `postgres` / DB: `weaponeering` |

---

## 🔑 การเข้าสู่ระบบเพื่อทดสอบ (Login & Bypass OTP สำหรับนักพัฒนา)

เพื่อให้สามารถทดสอบระบบได้ทันทีโดยไม่ต้องเชื่อมต่อกับเครือข่ายภายใน ทอ. (RTAF Super App MFA):
1. เปิดหน้าเว็บไปที่ `http://localhost:5173/login`
2. กรอกอีเมลใดก็ได้ (เช่น `admin@rtaf.mi.th`) แล้วกดขอรหัส OTP
3. กรอกรหัส OTP สำหรับทดสอบ: **`123456`** หรือ **`000000`**
   *(หรือคลิกปุ่ม **"⚡ Bypass เข้าสู่ระบบทันที (Admin Test)"** บนหน้า Login)*

> **หมายเหตุสำหรับขึ้น Production**: โค้ดส่วน Dev OTP Bypass อยู่ในไฟล์ `weaponeering-backend/src/weaponeering_api/services/rtaf_mfa.py` บรรทัดที่ `39–59` ระหว่างคอมเมนต์ `# [DEV-TEMP-START]` ถึง `# [DEV-TEMP-END]`

---

## ✨ ฟีเจอร์หลักที่พัฒนาเพิ่มเติมในเวอร์ชันนี้

1. **AI Assistant Chatbot เชื่อมต่อ RAG Platform API จริง (`RightPanel.vue`)**:
   - เพิ่มปุ่มไอคอนรูปฟันเฟือง (`⚙️`) ที่มุมขวาของหัวข้อ `AI Assistant (Chatbot ถามตอบ)`
   - กดเพื่อเปิดช่องตั้งค่า **POST URL / Port** (เช่น `http://localhost:1152/v1/chat/completions`, `http://localhost:1152/chat` หรือใส่เฉพาะเลขพอร์ต `1152`) และช่อง **API Key** (`Bearer` / `X-API-Key`) ตามคู่มือ [`api-manual.md`](api-manual.md)
   - รองรับการแสดงผลแบบไหลทีละคำ (**SSE Live Streaming**), แสดงรายการเอกสารอ้างอิง (**Citations**), ปุ่มทดสอบการเชื่อมต่อ (`ทดสอบ`) และจดจำการตั้งค่าลง `localStorage`
2. **หน้าจอ `3D Mission Simulator` (`SimulatorDemo.vue`)**:
   - แยกการทำงานอิสระ 100% จากแผนที่หลักตรงกลาง (`MapPanel.vue`)
   - **กล่องพื้นที่เป้าหมาย 3 มิติ (`Target Footprint Box`) แสดงอยู่ตลอดเวลาทุกจุด**
   - เลือกดู **วงรัศมีทำลายล้าง (`Effect Radius Rings & 3D Domes`)** ของแต่ละจุดเป้าหมายได้ทั้งแบบสลับดูทีละเป้าหมาย (`<` `>`) หรือดูพร้อมกันทุกเป้าหมาย (`ดูทุกจุด`) พร้อมมุมกล้องหมุน 360°
3. **ฐานข้อมูล `pgpool` พร้อมเป้าหมายตัวอย่าง 3 มิติ**:
   - มี Scenario ตัวอย่าง **`ภารกิจทดสอบยุทธการ (Scenario ตัวอย่าง)`** พร้อมเป้าหมาย 3 มิติ 4 จุด (คลังแสง, อาคารศูนย์บัญชาการ, โรงเก็บอากาศยาน, สถานีเรดาร์) ที่ตั้งค่าขนาด กว้าง×ยาว×สูง และคำนวณค่ารัศมี JMEM ไว้ครบถ้วนแล้ว
