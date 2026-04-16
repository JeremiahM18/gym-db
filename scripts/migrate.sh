#!/usr/bin/env bash
# Apply numbered SQL migrations in order, skipping any already applied.
#
# Usage:
#   ./scripts/migrate.sh [DATABASE_URL]
#
# DATABASE_URL defaults to the local bootstrap/admin DSN when omitted.
#
# The script creates a _migrations table in the public schema on first run
# and records every applied migration by filename. Re-running is safe: files
# already in the table are skipped. Seed files (9xx_*.sql) are never applied
# automatically; pass --seed to include them.
#
# Example (local dev):
#   ./scripts/migrate.sh
#
# Example (explicit DSN):
#   ./scripts/migrate.sh "postgresql://gymdb:gymdb_password@localhost:5432/gymdb"
#
# Example (apply seed data too, local only):
#   ./scripts/migrate.sh --seed

set -euo pipefail

SEED=false
DATABASE_URL="postgresql://gymdb:gymdb_password@localhost:5432/gymdb"
SCHEMA_DIR="$(cd "$(dirname "$0")/../database/schema" && pwd)"

run_psql() {
  if command -v psql >/dev/null 2>&1; then
    psql "$DATABASE_URL" "$@"
    return
  fi

  if command -v docker >/dev/null 2>&1; then
    docker compose exec -T postgres psql "$DATABASE_URL" "$@"
    return
  fi

  echo "psql is not installed and Docker fallback is unavailable." >&2
  exit 1
}

for arg in "$@"; do
  case "$arg" in
    --seed) SEED=true ;;
    *) DATABASE_URL="$arg" ;;
  esac
done

run_psql -v ON_ERROR_STOP=1 -q <<'SQL'
CREATE TABLE IF NOT EXISTS public._migrations (
    filename TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
SQL

echo "Scanning $SCHEMA_DIR for migrations..."

applied=0
skipped=0

existing_applied_count=$(run_psql -tAq -c "SELECT COUNT(*) FROM public._migrations")
docker_initialized_schema=$(run_psql -tAq <<'SQL'
SELECT CASE
    WHEN to_regclass('public.gyms') IS NOT NULL
     AND to_regclass('ops.job_receipts') IS NOT NULL
    THEN 1
    ELSE 0
END
SQL
)

if [[ "$existing_applied_count" == "0" ]] && [[ "$docker_initialized_schema" == "1" ]]; then
  echo "Detected an existing Docker-initialized schema with no migration history."
  echo "Baselining non-seed migrations into public._migrations..."

  for file in "$SCHEMA_DIR"/[0-8][0-9][0-9]_*.sql; do
    filename="$(basename "$file")"
    run_psql -q \
      -c "INSERT INTO public._migrations (filename) VALUES ('$filename') ON CONFLICT (filename) DO NOTHING"
  done
fi

for file in "$SCHEMA_DIR"/[0-9][0-9][0-9]_*.sql; do
  filename="$(basename "$file")"

  # Skip seed files unless --seed was passed
  if [[ "$filename" == 9[0-9][0-9]_* ]] && [[ "$SEED" != true ]]; then
    continue
  fi

  already_applied=$(run_psql -tAq \
    -c "SELECT 1 FROM public._migrations WHERE filename = '$filename'")

  if [[ "$already_applied" == "1" ]]; then
    echo "  skip   $filename"
    skipped=$((skipped + 1))
    continue
  fi

  echo "  apply  $filename"
  run_psql -v ON_ERROR_STOP=1 -q < "$file"
  run_psql -q \
    -c "INSERT INTO public._migrations (filename) VALUES ('$filename')"
  applied=$((applied + 1))
done

echo "Done: $applied applied, $skipped skipped."
