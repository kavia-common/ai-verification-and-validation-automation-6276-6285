#!/usr/bin/env bash
set -euo pipefail

# Simple backup script supporting SQLite (default) and PostgreSQL via DATABASE_URL
# Usage: ./scripts/backup_db.sh [output_dir]
OUT_DIR="${1:-backups}"
mkdir -p "$OUT_DIR"

DATE_TAG="$(date +%Y%m%d_%H%M%S)"
DB_URL="${DATABASE_URL:-}"

if [[ -z "$DB_URL" ]]; then
  # SQLite default at instance/app.db
  DB_PATH="$(pwd)/instance/app.db"
  if [[ ! -f "$DB_PATH" ]]; then
    echo "SQLite DB not found at $DB_PATH"
    exit 1
  fi
  OUT_FILE="${OUT_DIR}/sqlite_backup_${DATE_TAG}.db"
  cp "$DB_PATH" "$OUT_FILE"
  echo "SQLite backup written to $OUT_FILE"
else
  # PostgreSQL pg_dump
  OUT_FILE="${OUT_DIR}/postgres_backup_${DATE_TAG}.sql"
  if ! command -v pg_dump >/dev/null 2>&1; then
    echo "pg_dump not found. Please install PostgreSQL client tools."
    exit 1
  fi
  PGPASSWORD="" pg_dump --no-owner --no-privileges --format=plain "$DB_URL" > "$OUT_FILE"
  echo "PostgreSQL backup written to $OUT_FILE"
fi
