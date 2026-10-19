#!/bin/sh
set -e

echo "Waiting for database (timeout 90s)..."
PYTHONPATH=/app/src python - <<'PY'
import os
import sys
import time

import psycopg

host = os.getenv("DB_HOST", "pgpool")
port = int(os.getenv("DB_PORT", "5432"))
name = os.getenv("DB_NAME", "weaponeering")
user = os.getenv("DB_USER") or "postgres"
password = os.getenv("DB_PASSWORD") or ""

deadline = time.time() + 90
last_err = None
while time.time() < deadline:
    try:
        with psycopg.connect(
            host=host,
            port=port,
            dbname=name,
            user=user,
            password=password,
            connect_timeout=5,
        ) as conn:
            conn.execute("SELECT 1")
        print(f"Database ready at {host}:{port}/{name}")
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        last_err = exc
        print(f"DB not ready yet ({host}:{port}): {exc}")
        time.sleep(3)

print(
    f"ERROR: database not reachable within 90s at {host}:{port}/{name}: {last_err}",
    file=sys.stderr,
)
print(
    "Start pgpool/postgres on shared-postgres-network, or set DB_HOST in weaponeering-backend/.env",
    file=sys.stderr,
)
sys.exit(1)
PY

echo "Running database migrations..."
# /app/alembic (migration scripts) shadows the installed package when cwd=/app.
# Probe and install from /tmp so we import the real alembic distribution.
cd /tmp
if ! python -c "from alembic.config import main" >/dev/null 2>&1; then
  echo "Installing alembic..."
  pip install -q "alembic>=1.14"
fi

PYTHONPATH=/app/src python - <<'PY'
from alembic.config import main

main(argv=["-c", "/app/alembic.ini", "upgrade", "head"])
PY

echo "Starting Weaponeering API (development) with reload..."
cd /app
exec uvicorn weaponeering_api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --reload-dir /app/src
