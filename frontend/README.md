# GymDB Frontend

This frontend is the primary demo surface for the GymDB backend.

## What It Does

The app lets a user:
- browse published gym records from `/v2/gyms`
- filter by confidence, tier, specialty, 24/7 access, and lifter friendliness
- run nearby search through `/v2/gyms` using `lat`, `lon`, and `radius_m`
- inspect a single gym's structured inference and source-backed metadata
- open gym websites when OSM tags provide them
- jump to Google Maps or OpenStreetMap for the selected gym
- see city/state and distance-in-miles in the result flow
- use the geo canvas to select gyms from a live coordinate projection
- see backend liveness and readiness at a glance

## Commands

- `npm run dev`
  Start the Vite development server.

- `npm run lint`
  Run frontend linting.

- `npm run build`
  Build the frontend bundle.

- `npm run generate:api`
  Regenerate the typed API client from the backend OpenAPI document.

## Environment

The frontend reads `VITE_API_BASE_URL`.

Example local setup in `src/.env.local`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Run Locally

1. Start the backend from `backend/`.
2. If you are not using Cognito locally, set `ENABLE_DEV_AUTH_BYPASS=true` in `backend/.env`.
3. Run `npm install` in `frontend/`.
4. Run `npm run dev`.
5. Open the local Vite URL shown in the terminal.
6. Hard refresh if the browser cached an older frontend bundle.
