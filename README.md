# GymDB

GymDB is a backend-first geospatial data platform for discovering, normalizing, enriching, and serving gym location data.

The project combines a FastAPI backend, PostGIS-backed spatial querying, deterministic inference, provenance-aware review workflows, and a React browser client that demonstrates the public API on top of published datasets.

This is not a CRUD demo. It is a systems-oriented project focused on data quality, stable contracts, explainability, and operational discipline.

## What Problem It Solves

There is no single clean, authoritative database of gyms.

Public sources such as OpenStreetMap are useful, but they are noisy:

- the same gym can appear multiple times
- names and tags are inconsistent
- business metadata is often missing or incomplete
- nearby search needs real geospatial correctness, not rough math
- downstream apps need stable contracts, not shifting response shapes

GymDB exists to turn messy location data into a trustworthy platform that downstream clients can browse, query, audit, and build on.

## Why This Project Is Strong

- Backend-first architecture with clear boundaries between domain, application, infrastructure, database, and API layers
- Real geospatial querying with PostgreSQL + PostGIS
- Deterministic, explainable inference instead of opaque heuristics
- Stable versioned API contracts with generated frontend client bindings
- Review workflows for matched, mismatched, and unconfirmed coverage results
- Job receipts and operational auditability for ingest runs
- CI-backed quality gates across backend and frontend

## Implemented Today

GymDB already includes:

- a FastAPI public API under `/v2`
- a separate internal job surface for controlled ingestion and job receipt inspection
- deterministic dataset publication and read-model access
- PostGIS nearby search using exact radius filtering and indexed candidate ordering
- rule-based inference with reasons, confidence scoring, and contradiction diagnostics
- TomTom-backed publish validation that gates ingest when external verification is unavailable
- coverage review endpoints for audit-style inspection of source agreement
- a React/Vite frontend that exercises the public API and shows inference details visually
- database schema and migration scripts for canonical gyms and job receipts
- backend tests covering API contracts, inference, determinism, nearby search, review flows, deduplication, persistence, and error handling

## Tech Stack

- Python 3.13
- FastAPI
- Pydantic v2
- SQLAlchemy
- PostgreSQL 16 + PostGIS
- React 19
- TypeScript
- Vite
- ESLint
- Pytest
- Ruff
- MyPy
- GitHub Actions

## Architecture

```text
OpenStreetMap / Secondary Public Sources
                |
                v
      Ingest + Normalize + Deduplicate
                |
                v
   Deterministic Inference + Coverage Review
                |
                +-----------------------------+
                |                             |
                v                             v
 PostgreSQL/PostGIS                    Published JSON datasets
  - canonical facts                    SQLite read-model sidecars
  - spatial indexes                    dataset manifests
  - job receipts                              |
                |                             |
                +-------------+---------------+
                              |
                              v
                     FastAPI Public API (/v2)
                              |
                              v
                     React Browser Client
```

## Public API Examples

The public API is versioned and treated as a contract.

### List gyms

```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/v2/gyms?region=tn_nashville&min_conf=0.6&specialty=powerlifting&limit=20"
```

### Run nearby search

```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/v2/gyms?lat=36.1627&lon=-86.7816&radius_m=2500&limit=25"
```

### Get one gym with inference details

```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/v2/gyms/gym_123?region=tn_nashville"
```

### Review source coverage

```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/v2/review/coverage?status=unconfirmed&contradictions_only=true"
```

If you enable `ENABLE_DEV_AUTH_BYPASS=true` locally, you can exercise the frontend and public endpoints without Cognito during development.

## Frontend Demo Surface

The frontend is not filler. It is a real operator/demo client for the backend.

It supports:

- catalog browsing over `/v2/gyms`
- city and place-name resolution through `/v2/geocode` before nearby search
- published-dataset nearby search using coordinates and radius filters
- filtering by confidence, tier, specialty, 24/7 access, and lifter friendliness
- drill-in inspection of inference details, confidence, and reasons
- source-backed actions like website, phone, Google Maps, and OpenStreetMap
- a geo canvas that renders result coordinates into an interactive map-like panel
- service liveness and readiness visibility from the browser

## Database Story

The database is a first-class part of the system, not just a persistence afterthought.

Current database design includes:

- PostgreSQL + PostGIS for durable geospatial storage
- canonical gym storage with spatial indexes
- exact nearby lookup support using spatial SQL
- deterministic schema evolution through checked-in SQL files
- operational job receipt persistence
- a dedicated local runtime role for the app instead of using the bootstrap database user directly

GymDB also deliberately separates durable operational facts in PostgreSQL from published read-only dataset artifacts and SQLite sidecars under `backend/data/`.

## Repository Layout

```text
gym-db/
  backend/
    api/                 FastAPI entrypoints, auth, versioned routes
    src/gymdb/domain/    Deterministic business logic and models
    src/gymdb/application/
    src/gymdb/infrastructure/
    src/gymdb/infer/     Rule engine primitives and inference helpers
    src/gymdb/observe/   Metrics, audit, and summaries
    tests/               Backend tests and contract coverage
    docs/                Inference and API contract notes
  database/
    schema/              SQL schema and migration scripts
    bootstrap/           Local/dev bootstrap SQL
  frontend/
    src/                 React browser client
```

## Quality and Verification

GymDB is strongest when judged as an engineering project, not just a feature checklist.

The repo includes:

- backend tests for API contracts, inference, determinism, query logic, nearby search, receipts, and review flows
- backend coverage reporting so regressions show both failures and blind spots
- strict linting and typing setup in the backend
- frontend linting, generated-client drift checks, and mocked browser E2E checks
- CI that runs backend and frontend quality gates
- a PostGIS-backed CI service so geospatial behavior is validated in a realistic environment
- migration verification in CI so schema changes cannot drift from a fresh database
- pre-commit / pre-push hooks for local guardrails before code reaches CI

Backend quality commands:

```bash
cd backend
python -m pytest --cov=api --cov=src/gymdb --cov-report=term-missing
ruff check .
mypy src/gymdb api
```

Frontend quality commands:

```bash
cd frontend
npm run lint
npm run build
npm run test:e2e
npm run verify:api-client
npm run generate:api
```

The API client generation script exports the backend OpenAPI schema from the checked-out FastAPI app and regenerates the frontend SDK locally, so the frontend contract stays aligned with the repo instead of a separately running server. CI now also verifies both sides of that contract with visible diffs: the checked-in `backend/openapi.json` must match the live FastAPI app, and the checked-in frontend SDK must match the checked-in schema.

Developer hooks:

```bash
cd backend
python -m pip install -r requirements-dev.txt
pre-commit install
pre-commit install --hook-type pre-push
```

## Run Locally

### 1. Start PostgreSQL + PostGIS

```bash
docker compose up -d postgres
```

Docker Compose auto-applies all files in `database/schema/` on the **first** start (when the volume is empty).
For subsequent schema changes on an existing volume, use the migration runner:

```bash
./scripts/migrate.sh
```

`migrate.sh` defaults to the local bootstrap database user (`gymdb`) because schema changes and `_migrations` bookkeeping require elevated database permissions. The backend runtime role remains `gymdb_app`.

For a completely fresh local database after schema or role changes, recreate the volume:

```bash
docker compose down -v
docker compose up -d postgres
```

### 2. Configure the backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Or bootstrap the local env files automatically from the repo root:

```powershell
.\scripts\bootstrap-local.ps1
```

The checked-in `backend/.env.example` already enables local dev auth bypass. If you want to confirm the expected local values, `backend/.env` should include:

```env
ENABLE_DEV_AUTH_BYPASS=true
POSTGRES_DSN=postgresql+psycopg://gymdb_app:gymdb_app_password@localhost:5432/gymdb
REQUIRE_TOMTOM_PUBLISH_VALIDATION=true
# Required for ingest / publish flows:
TOMTOM_API_KEY=<your tomtom api key>
```

TomTom validation is now the default publish gate. If you are browsing an already-published dataset locally, you do not need a TomTom key. If you are rebuilding a dataset, configure `TOMTOM_API_KEY` first.
If Overpass is under load, the ingest client now retries automatically and can fail over to an alternate endpoint if you set `OVERPASS_FALLBACK_URL`. A smaller `--radius-miles` is still the fastest way to get an initial local dataset published.

Then start the API:

```bash
python -m uvicorn api.main:app --reload
```

Important: the backend is currently configured with `data/`-relative paths, so start it from the `backend/` directory unless you override those settings explicitly.

### 3. Start the frontend

```bash
cd frontend
npm install
```

The frontend is standardized on Node 24 to match CI. If you use `nvm`, run `nvm use` from the repo root before installing frontend dependencies.
If backend routes or schemas changed, run `npm run generate:api` after the backend virtualenv is set up so the frontend SDK is regenerated from the checked-out FastAPI app.
If you want to run browser E2E checks locally, install the browser once with `npm run test:e2e:install`.

Create `frontend/.env.local`:

```env
VITE_API_BASE_URL=http://localhost:8000
# Optional when dev auth bypass is disabled:
# VITE_API_TOKEN=<bearer token>
```

Then run:

```bash
npm run dev
```

## Contracts and Design Notes

- Backend API stability notes: [backend/docs/api_status.md](backend/docs/api_status.md)
- Inference contract: [backend/docs/inference.md](backend/docs/inference.md)
- Database design notes: [database/README_DATABASE.md](database/README_DATABASE.md)

## Local Security Model

For local development, GymDB now distinguishes between:

- the container bootstrap database user, which initializes schema objects
- the app runtime role, `gymdb_app`, which the backend uses through `POSTGRES_DSN`

That is still a development setup, but it is cleaner than running the application as the bootstrap user and better reflects production-minded separation of concerns.

## What This Project Demonstrates

GymDB shows the kind of engineering work that matters in backend and systems-heavy roles:

- designing stable interfaces instead of ad hoc responses
- treating data quality and provenance as product features
- separating durable facts from derived interpretations
- building geospatial and operational concerns into the architecture early
- using tests and contracts to protect behavior over time

It is not “done,” but it is already a serious, credible project with clear depth.
