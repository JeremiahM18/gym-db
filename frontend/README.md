# GymDB Frontend

This frontend is the main product surface for GymDB.

## What It Does

The app lets a user:
- start with nearby search from `/v2/live/search`
- browse a tighter curated shortlist from `/v2/gyms`
- search by place without exposing raw latitude/longitude fields in the UI
- compare gyms in a map-first, nearby-first discovery workspace
- inspect live gyms as OpenStreetMap-first results with GymDB inference and TomTom verification/enrichment
- inspect published gyms with structured inference, field-level confidence, contradiction diagnostics, source provenance, and source-backed metadata
- open gym websites when OSM tags provide them
- jump to Google Maps or OpenStreetMap for the selected gym
- see city/state, distance-in-miles, hours, website, phone, and other trust signals in the result flow
- use the map surface to select gyms from a live coordinate projection
- see backend liveness and readiness at a glance
- browse against your local published dataset artifacts and current scoring model without committing local data to git
- build on a backend review API that can power matched, mismatched, and unconfirmed coverage dashboards

## Commands

- `npm run dev`
  Start the Vite development server.

- `npm run lint`
  Run frontend linting.

- `npm run build`
  Build the frontend bundle.

- `npm run test:e2e`
  Run the mocked Playwright browser flows against the local Vite app.

- `npm run test:e2e:install`
  Install the Chromium browser used by the Playwright suite.

- `npm run generate:api`
  Regenerate the typed API client from the checked-out backend using `backend/.venv`.

- `npm run verify:api-client`
  Rebuild the generated client from the checked-in backend OpenAPI snapshot and fail if committed SDK files drifted.

## Environment

The frontend reads `VITE_API_BASE_URL`.
For live search, the backend must also have `TOMTOM_API_KEY` configured.

The frontend is standardized on Node 24 to match CI.
If you use `nvm`, run `nvm use` from the repo root before installing dependencies.
Nearby search in the browser does not publish a new dataset by itself. The curated shortlist remains a separate product surface backed by published dataset artifacts. To publish a different city into that catalog, run the backend ingest CLI with `--place`.

Example local setup in `.env.local`:

```env
VITE_API_BASE_URL=http://localhost:8000
# Optional when backend auth bypass is disabled:
# VITE_API_TOKEN=<bearer token>
```

## Run Locally

1. Start the backend from `backend/`.
2. Copy `backend/.env.example` to `backend/.env`.
3. If you want to work locally without Cognito, explicitly set `ENABLE_DEV_AUTH_BYPASS=true` in your untracked `backend/.env`.
4. Run `npm install` in `frontend/`.
5. If backend routes or schemas changed, run `npm run generate:api`. This expects a configured `backend/.venv` because the schema is exported from the checked-out FastAPI app.
6. If you plan to run browser E2E checks locally, run `npm run test:e2e:install` once.
7. Run `npm run dev`.
8. Open the local Vite URL shown in the terminal.
9. Hard refresh if the browser cached an older frontend bundle.
