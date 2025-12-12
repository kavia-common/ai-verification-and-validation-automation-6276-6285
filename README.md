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

Local (Python) backend only:
1) Install dependencies
   pip install -r test_automation_backend/requirements.txt

2) Set environment (optional)
   export DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname
   export FRONTEND_ORIGIN=http://localhost:3000  # to enable CORS from the UI

3) Initialize DB schema
   cd test_automation_backend
   # Option A: Alembic migrations
   alembic upgrade head
   # Option B: Dev-only create tables
   flask --app app.app_factory:create_app create-db

4) Start the app (example)
   flask --app app.app_factory:create_app run -p 3001

5) API Docs
   Swagger/OpenAPI available at /docs

Docker Compose (backend + optional postgres + frontend):
1) Copy example envs and adjust as needed
   cp test_automation_backend/.env.example test_automation_backend/.env
   cp test_automation_ui/.env.example test_automation_ui/.env

2) Build and start
   docker compose up --build

   Services:
   - Backend: http://localhost:3001
   - Frontend: http://localhost:3000
   - Postgres (optional): 5432 (internal service "db")

3) Database selection
   By default, backend connects to the "db" Postgres service via DATABASE_URL from compose.
   To use SQLite instead, set DATABASE_URL empty in test_automation_backend/.env or remove it in compose.

4) Storage and instance directory
   Backend writes SQLite DB and artifacts under test_automation_backend/instance/ (persisted via a named volume).
   Ensure instance and storage directories are available; container startup creates them automatically.

5) CORS
   Backend CORS is restricted via FRONTEND_ORIGIN (default http://localhost:3000). Adjust FRONTEND_ORIGIN env for deployments.

6) Mocks and auth flags
   - USE_LLM_MOCK=true to use mock LLM (maps to MOCK_LLM env)
   - EXECUTION_MODE=mock to avoid running pytest/playwright (maps to MOCK_EXECUTION=true)
   - AUTH_DISABLED=true disables auth checks for early development

7) Environment variables
   - Frontend expects REACT_APP_API_BASE_URL to point to the backend (default http://localhost:3001). Set in .env or compose build args.

### Runtime toggles

These env vars let you run without external services:
- MOCK_LLM=true (default): use a mock LLM to generate test cases.
- MOCK_EXECUTION=true (default): mark executions as passed without invoking pytest.

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