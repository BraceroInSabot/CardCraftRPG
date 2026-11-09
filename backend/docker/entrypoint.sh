#!/bin/sh
# Prepare the database, then start the command given as CMD (Gunicorn by default).
set -e

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  attempt=1
  until python manage.py migrate --noinput; do
    if [ "$attempt" -ge 10 ]; then
      echo "The database is still unreachable after $attempt attempts. Check the POSTGRES_* settings." >&2
      exit 1
    fi
    echo "Waiting for the database (attempt $attempt)..."
    attempt=$((attempt + 1))
    sleep 3
  done
fi

if [ "${SEED_DEMO:-false}" = "true" ]; then
  python manage.py seed_demo
fi

exec "$@"
