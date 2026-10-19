#!/bin/sh
set -e

cd /app

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
        print(f"DB not ready yet: {exc}")
        time.sleep(3)

print(f"ERROR: database not reachable within 90s: {last_err}", file=sys.stderr)
sys.exit(1)
PY

echo "Running database migrations..."
# Use absolute path — cwd has ./alembic/ (migration scripts) which can shadow the package
PYTHONPATH=/app/src /usr/local/bin/alembic -c /app/alembic.ini upgrade head

WORKERS=${WORKERS:-2}

echo "Starting Weaponeering API (production) on port 8000..."
exec uvicorn weaponeering_api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "$WORKERS" \
    --timeout-keep-alive 120
