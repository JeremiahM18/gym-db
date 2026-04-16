# GymDB Frontend

This frontend is the primary demo surface for the GymDB backend.

## What It Does

The app lets a user:
- browse published gym records from `/v2/gyms`
- filter by confidence, tier, specialty, 24/7 access, and lifter friendliness
- run nearby search through `/v2/gyms` using `lat`, `lon`, and `radius_m`
- inspect a single gym's structured inference, field-level confidence, contradiction diagnostics, source provenance, and source-backed metadata
- open gym websites when OSM tags provide them
- jump to Google Maps or OpenStreetMap for the selected gym
- see city/state and distance-in-miles in the result flow
- use the geo canvas to select gyms from a live coordinate projection
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

- `npm run generate:api`
  Regenerate the typed API client from the checked-out backend using `backend/.venv`.

## Environment

The frontend reads `VITE_API_BASE_URL`.

The frontend is standardized on Node 24 to match CI.
If you use `nvm`, run `nvm use` from the repo root before installing dependencies.

Example local setup in `.env.local`:

```env
VITE_API_BASE_URL=http://localhost:8000
# Optional when backend auth bypass is disabled:
# VITE_API_TOKEN=<bearer token>
```

## Run Locally

1. Start the backend from `backend/`.
2. The checked-in `backend/.env.example` already enables local dev auth bypass for local work.
3. Run `npm install` in `frontend/`.
4. If backend routes or schemas changed, run `npm run generate:api`. This expects a configured `backend/.venv` because the schema is exported from the checked-out FastAPI app.
5. Run `npm run dev`.
6. Open the local Vite URL shown in the terminal.
7. Hard refresh if the browser cached an older frontend bundle.
