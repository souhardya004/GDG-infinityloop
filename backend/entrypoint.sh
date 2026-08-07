#!/bin/sh
set -e

wait_for_db() {
  if [ -z "${DATABASE_URL:-}" ]; then
    return 0
  fi

  echo "Waiting for PostgreSQL..."
  python - <<'PY'
import os
import sys
import time

import dj_database_url
import psycopg

cfg = dj_database_url.parse(os.environ["DATABASE_URL"])
for attempt in range(60):
    try:
        conn = psycopg.connect(
            host=cfg.get("HOST") or "",
            port=cfg.get("PORT") or 5432,
            user=cfg.get("USER") or "",
            password=cfg.get("PASSWORD") or "",
            dbname=cfg.get("NAME") or "",
        )
        conn.close()
        print("PostgreSQL is ready.")
        sys.exit(0)
    except Exception as exc:
        if attempt == 59:
            print(f"PostgreSQL unavailable: {exc}", file=sys.stderr)
            sys.exit(1)
        time.sleep(1)
PY
}

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  wait_for_db
  python manage.py migrate --noinput
fi

exec "$@"
