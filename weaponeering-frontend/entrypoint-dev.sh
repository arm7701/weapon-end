#!/bin/sh
set -e

cd /app

# Keep named node_modules volume in sync when package-lock.json changes.
LOCK_HASH_FILE="/app/node_modules/.package-lock.sha"
CURRENT_HASH="$(sha256sum package-lock.json 2>/dev/null | awk '{print $1}')"
STORED_HASH="$(cat "$LOCK_HASH_FILE" 2>/dev/null || true)"

if [ ! -d node_modules ] || [ "$CURRENT_HASH" != "$STORED_HASH" ]; then
  echo "[frontend] Installing npm dependencies..."
  npm ci
  echo "$CURRENT_HASH" > "$LOCK_HASH_FILE"
fi

exec npm run dev -- --host 0.0.0.0 --port 3000
