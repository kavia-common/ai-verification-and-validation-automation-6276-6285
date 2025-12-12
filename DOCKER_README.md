# AI V&V Test Automation - Docker Quickstart

This repository provides dockerized development for:
- backend (Flask API) on port 3001
- frontend (React) on port 3000
- optional PostgreSQL database

## Prerequisites
- Docker and Docker Compose

## Setup

1) Copy .env examples:
   cp test_automation_backend/.env.example test_automation_backend/.env
   cp test_automation_ui/.env.example test_automation_ui/.env

2) Start the stack:
   docker compose up --build

   Services:
   - Backend: http://localhost:3001
   - Frontend: http://localhost:3000
   - Postgres: internal service 'db' on port 5432

3) Database configuration
   - Default: Postgres via DATABASE_URL in docker-compose
   - To use SQLite, clear DATABASE_URL (empty) in test_automation_backend/.env

4) CORS
   Set FRONTEND_ORIGIN (default http://localhost:3000) to restrict allowed frontend origin.

5) Mock toggles and auth flags
   - USE_LLM_MOCK=true enables LLM mock mode (maps to MOCK_LLM)
   - EXECUTION_MODE=mock avoids real pytest execution (maps to MOCK_EXECUTION=true)
   - AUTH_DISABLED=true disables auth checks for development

6) Frontend API base URL
   React app reads REACT_APP_API_BASE_URL (default http://localhost:3001). Update as needed.

7) Persistence
   The backend instance directory (SQLite DB and artifacts) is persisted via a named volume (backend_instance).

## Common commands
- Stop: docker compose down
- Rebuild: docker compose build --no-cache
- Logs: docker compose logs -f backend
- DB migrations in container:
  docker compose exec backend alembic upgrade head
