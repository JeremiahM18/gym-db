#!/usr/bin/env bash
# Apply numbered SQL migrations in order, skipping any already applied.
#
# Usage:
#   ./scripts/migrate.sh [DATABASE_URL]
#
# DATABASE_URL defaults to the local dev DSN when omitted.
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
#   ./scripts/migrate.sh "postgresql://gymdb_app:gymdb_app_password@localhost:5432/gymdb"
#
# Example (apply seed data too, local only):
#   ./scripts/migrate.sh --seed

set -euo pipefail

SEED=false
DATABASE_URL="postgresql://gymdb_app:gymdb_app_password@localhost:5432/gymdb"
SCHEMA_DIR="$(cd "$(dirname "$0")/../database/schema" && pwd)"

for arg in "$@"; do
  case "$arg" in
    --seed) SEED=true ;;
    *) DATABASE_URL="$arg" ;;
  esac
done

psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -q <<'SQL'
CREATE TABLE IF NOT EXISTS public._migrations (
    filename TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
SQL

echo "Scanning $SCHEMA_DIR for migrations..."

applied=0
skipped=0

for file in "$SCHEMA_DIR"/[0-9][0-9][0-9]_*.sql; do
  filename="$(basename "$file")"

  # Skip seed files unless --seed was passed
  if [[ "$filename" == 9[0-9][0-9]_* ]] && [[ "$SEED" != true ]]; then
    continue
  fi

  already_applied=$(psql "$DATABASE_URL" -tAq \
    -c "SELECT 1 FROM public._migrations WHERE filename = '$filename'")

  if [[ "$already_applied" == "1" ]]; then
    echo "  skip   $filename"
    skipped=$((skipped + 1))
    continue
  fi

  echo "  apply  $filename"
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -q -f "$file"
  psql "$DATABASE_URL" -q \
    -c "INSERT INTO public._migrations (filename) VALUES ('$filename')"
  applied=$((applied + 1))
done

echo "Done: $applied applied, $skipped skipped."
