#!/usr/bin/env bash
set -euo pipefail

# Simple restore script supporting SQLite (default) and PostgreSQL via DATABASE_URL
# Usage: ./scripts/restore_db.sh <backup_file>
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <backup_file>"
  exit 1
fi

BACKUP_FILE="$1"
DB_URL="${DATABASE_URL:-}"

if [[ -z "$DB_URL" ]]; then
  # SQLite restore
  DB_PATH="$(pwd)/instance/app.db"
  mkdir -p "$(dirname "$DB_PATH")"
  cp "$BACKUP_FILE" "$DB_PATH"
  echo "SQLite DB restored to $DB_PATH"
else
  # PostgreSQL restore
  if ! command -v psql >/dev/null 2>&1; then
    echo "psql not found. Please install PostgreSQL client tools."
    exit 1
  fi
  psql "$DB_URL" -f "$BACKUP_FILE"
  echo "PostgreSQL DB restored from $BACKUP_FILE"
fi
