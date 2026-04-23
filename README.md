# GymDB

GymDB is a full-stack gym discovery product and data platform. It combines a FastAPI backend, a PostGIS-backed published catalog, a TomTom-backed live-search flow, deterministic inference, provenance-aware enrichment, and a React browser client.

The project has two user-facing search surfaces:

- published catalog browsing over `/v2/gyms`
- live place search over `/v2/live/search`

Those surfaces solve different problems and are implemented differently on purpose.

## Product Surface

### Published catalog

The published catalog is the stable, curated browse surface.

- backed by checked-in dataset artifacts under `backend/data/`
- queryable through `/v2/gyms`
- supports region, specialty, tier, confidence, and nearby-style filtering
- suitable for deterministic browsing, review, and downstream integrations

### Live search

Live search is the nearby-first product flow for a user who wants gyms around a place right now.

Current behavior:

- TomTom resolves the place query
- TomTom returns the initial nearby gym snapshot
- GymDB deduplicates, scores, and annotates those results
- if a fresh local OSM cache is available, OSM confirmation is applied immediately
- if not, GymDB returns the TomTom-backed snapshot right away, creates a `search_id`, and schedules background Overpass enrichment
- the frontend polls `/v2/live/search/{search_id}` so the same results can improve in place without another TomTom call

OSM is therefore an enrichment and corroboration source in the live-search flow, not the primary online lookup for the initial response.

## Core Capabilities

- FastAPI public API under `/v2`
- TomTom-backed place resolution and initial live search
- OSM confirmation and metadata enrichment for live results
- PostGIS nearby querying for the published catalog
- deterministic rule-based inference with confidence and reasons
- provenance-aware coverage and review workflows
- job receipt persistence for ingest operations
- generated frontend SDK from the checked-in OpenAPI snapshot
- backend and frontend CI gates for linting, typing, tests, and contract drift

## Architecture

```text
                            +-------------------------+
                            |        Frontend         |
                            | React + generated SDK   |
                            +------------+------------+
                                         |
                                         v
                         +---------------+----------------+
                         |        FastAPI public API      |
                         | /v2/gyms, /v2/live/search, ... |
                         +---------------+----------------+
                                         |
                  +----------------------+----------------------+
                  |                                             |
                  v                                             v
      +-----------+-----------+                    +------------+-------------+
      | Published catalog     |                    | Live search session      |
      | PostgreSQL + PostGIS  |                    | TomTom snapshot + OSM    |
      | dataset artifacts     |                    | enrichment in background  |
      +-----------+-----------+                    +------------+-------------+
                  |                                             |
                  v                                             v
      checked-in / generated datasets                local cache + session files
      under backend/data/                            under backend/data/
```

## Repository Layout

```text
gym-db/
  backend/
    api/                 FastAPI routes, auth, dependencies
    src/gymdb/domain/    business logic and models
    src/gymdb/application/
    src/gymdb/infrastructure/
    src/gymdb/infer/     inference engine primitives
    src/gymdb/observe/   metrics, audit, summaries
    tests/               backend tests
    docs/                contract and design notes
    data/                datasets, cache, runtime artifacts
  database/
    schema/              SQL schema and migrations
  frontend/
    src/                 React application
    e2e/                 Playwright browser tests
  scripts/               repo-level bootstrap and helper scripts
```

## Public API

The public API is versioned and treated as a contract.

Primary routes:

- `GET /v2/gyms`
- `GET /v2/gyms/{gym_id}`
- `GET /v2/gyms/geo/nearby`
- `GET /v2/geocode`
- `GET /v2/live/search`
- `GET /v2/live/search/{search_id}`

Example calls:

```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/v2/gyms?region=tn_nashville&specialty=powerlifting&limit=20"
```

```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/v2/live/search?place=Franklin%2C%20TN&q=gym&radius_m=25000"
```

```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/v2/live/search/<search_id>"
```

Contract notes:

- the checked-in backend OpenAPI snapshot lives at `backend/openapi.json`
- the frontend generated client is derived from that snapshot
- CI verifies both the OpenAPI snapshot and the generated client for drift

See `backend/docs/api_status.md` for the detailed contract notes.

## Local Development

### 1. Start PostgreSQL + PostGIS

```bash
docker compose up -d postgres
```

On a fresh volume, Docker applies the checked-in SQL files automatically. On an existing volume, apply pending migrations with:

```bash
./scripts/migrate.sh
```

To rebuild the local database from scratch:

```bash
docker compose down -v
docker compose up -d postgres
```

### 2. Set up the backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Or bootstrap local env files from the repo root:

```powershell
.\scripts\bootstrap-local.ps1
```

Minimum backend settings for local development:

```env
ENABLE_DEV_AUTH_BYPASS=false
POSTGRES_DSN=postgresql+psycopg://gymdb_app:gymdb_app_password@localhost:5432/gymdb
REQUIRE_TOMTOM_PUBLISH_VALIDATION=true
TOMTOM_API_KEY=<your tomtom api key>
```

If you want to work locally without Cognito:

```env
ENABLE_DEV_AUTH_BYPASS=true
```

Start the API:

```bash
python -m uvicorn api.main:app --reload
```

Useful backend helpers:

- `backend/scripts/export_openapi.py` refreshes `backend/openapi.json`
- `backend/scripts/sync_dataset_to_postgres.py` syncs the shipped dataset into the local Postgres container
- `python .\src\main.py --place "Franklin, TN" --radius-miles 12 --region-key franklin_tn --set-default-region` ingests and publishes a new region by place name

### 3. Set up the frontend

```bash
cd frontend
npm install
```

The frontend is standardized on Node 24.

Create `frontend/.env.local`:

```env
VITE_API_BASE_URL=http://localhost:8000
# Optional when dev auth bypass is disabled:
# VITE_API_TOKEN=<bearer token>
```

Run the app:

```bash
npm run dev
```

If the backend contract changed:

1. refresh the backend OpenAPI snapshot
2. regenerate the frontend client

You can do both with the repo helper:

```powershell
.\scripts\generate-frontend-api.ps1
```

## Quality Gates

Backend:

```bash
cd backend
python -m pytest --cov=api --cov=src/gymdb --cov-report=term-missing
ruff check .
mypy src/gymdb api
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
npm run test:e2e
npm run verify:api-client
```

## Additional Docs

- API contract: `backend/docs/api_status.md`
- Inference contract: `backend/docs/inference.md`
- Database storage notes: `database/README_DATABASE.md`
- Dataset and runtime artifact rules: `backend/data/README.md`
