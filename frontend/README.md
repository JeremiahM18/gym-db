# GymDB Frontend

The frontend is the primary product UI for GymDB. It presents two distinct browse flows backed by the public API.

## User Flows

### Live search

Live search is the default nearby-first experience.

- users search by place and radius
- the initial snapshot comes from TomTom-backed live search
- if OSM enrichment is still pending, the frontend polls the saved `search_id`
- the same result list can improve in place as OSM confirmation and metadata arrive

### Curated catalog

The curated catalog is the stable published browse surface.

- backed by `/v2/gyms`
- supports filters such as specialty, tier, confidence, 24/7, and lifter friendliness
- intended for deterministic browsing over published dataset artifacts

## Commands

- `npm run dev`
  Start the Vite dev server.

- `npm run lint`
  Run ESLint.

- `npm run build`
  Build the production bundle.

- `npm run test:e2e`
  Run the Playwright suite.

- `npm run test:e2e:install`
  Install the Chromium browser used by Playwright.

- `npm run generate:api`
  Regenerate the typed frontend client from the checked-in `../backend/openapi.json` snapshot.

- `npm run verify:api-client`
  Regenerate the client and fail if the committed SDK differs from the checked-in snapshot.

## Environment

Required:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Optional when backend auth bypass is disabled:

```env
VITE_API_TOKEN=<bearer token>
```

Notes:

- the frontend targets Node 24 to match CI
- live search requires the backend to have `TOMTOM_API_KEY` configured
- the frontend does not publish datasets; it only consumes the public API

## Local Setup

1. Set up and start the backend from `../backend`.
2. Run `npm install`.
3. Create `frontend/.env.local`.
4. Run `npm run dev`.

If the backend contract changed:

1. refresh `backend/openapi.json`
2. regenerate the frontend client

From the repo root, the helper does both:

```powershell
.\scripts\generate-frontend-api.ps1
```

If you plan to run browser tests locally, install Playwright once:

```bash
npm run test:e2e:install
```
