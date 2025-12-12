# ai-verification-and-validation-automation-6276-6285

## Backend Database, Models, and Migrations

This backend is configured to use SQLAlchemy with environment-based configuration:
- Default: SQLite file database at instance/app.db
- Optional: PostgreSQL via DATABASE_URL (e.g., postgresql+psycopg2://user:pass@host:5432/dbname)

Key models:
- SRS, SRSVersion
- TestCase, TestScript
- TestRun, TestResult
- Artifact

### Quick start

1) Install dependencies
   pip install -r test_automation_backend/requirements.txt

2) Set environment (optional)
   export DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname

3) Initialize DB schema
   cd test_automation_backend
   # Option A: Alembic migrations
   alembic upgrade head
   # Option B: Dev-only create tables
   flask --app app.app_factory:create_app create-db

### Migrations

- Create new migration:
  alembic revision -m "change description"
- Apply migrations:
  alembic upgrade head
- Rollback latest:
  alembic downgrade -1

Alembic is preconfigured in test_automation_backend/alembic.ini with migration scripts in test_automation_backend/migrations/.

### Backup / Restore

- Backup:
  ./scripts/backup_db.sh
  # or provide output dir
  ./scripts/backup_db.sh backups/

- Restore:
  ./scripts/restore_db.sh <backup_file>

For PostgreSQL, ensure pg_dump and psql clients are available and DATABASE_URL is set.