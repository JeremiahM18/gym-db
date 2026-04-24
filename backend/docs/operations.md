# Operations

## Runtime Configuration

Shared settings come from `backend/.env` and `backend/.env.local`.

Core required settings:

- `POSTGRES_DSN`
- `CORS_ALLOWED_ORIGINS`
- Cognito settings for non-local auth:
  - `AWS_REGION`
  - `COGNITO_USER_POOL_ID`
  - `COGNITO_APP_CLIENT_ID`
  - `COGNITO_ISSUER`

Live-search settings:

- `TOMTOM_API_KEY` for TomTom-backed geocoding and initial live-search snapshots
- `TOMTOM_BASE_URL` for the upstream TomTom API origin
- `LIVE_SEARCH_CACHE_ROOT`
- `LIVE_SEARCH_SESSION_ROOT`
- `OPS_STATE_PATH`

Production and staging guards:

- `ENABLE_DEV_AUTH_BYPASS` must stay `false`
- Cognito settings must not use placeholder defaults
- `TOMTOM_BASE_URL` must use HTTPS
- `CORS_ALLOWED_ORIGINS` must not include localhost origins

The API now fails fast at startup if required local runtime dependencies are not usable.

## Startup Contract

Startup preflight validates:

- dataset registry loads
- default dataset file exists
- dataset root exists
- live-search cache root is writable
- live-search session root is writable
- shared ops-state SQLite store is writable

If any of those checks fail, the API should not start.

## Health Endpoints

### `GET /healthz`

Liveness only. This confirms the process is serving requests.

Current payload:

- `status`
- `api_version`
- `environment`

### `GET /readyz`

Readiness for traffic. This checks:

- database connectivity
- PostGIS availability
- required schema objects
- dataset registry/default dataset presence
- dataset root presence
- live-search cache/session storage writability
- ops-state store writability

`503` means the process is up but not safe to treat as ready.

## Metrics Endpoints

Internal lightweight JSON metrics currently exposed:

- `GET /metrics/http`
- `GET /metrics/inference`
- `GET /metrics/live-search`

Current HTTP metrics are intentionally low-cardinality:

- total requests
- 2xx, 4xx, and 5xx counts
- unhandled request exception count
- coarse latency buckets

Current live-search metrics include:

- cache hit, miss, and stale probes
- enrichment dispatch and outcome counts
- OSM confirmation tier distribution

These endpoints are useful for local operations and small deployments. For multi-host production, export the same signals to a centralized monitoring system.

## Release Checklist

Run before shipping:

1. Apply database migrations in a clean database.
2. Verify `backend/openapi.json` matches a fresh export.
3. Verify the frontend generated client matches the checked-in OpenAPI snapshot.
4. Run backend lint, typecheck, and tests.
5. Run frontend lint, build, and e2e tests.
6. Confirm required environment variables for the target environment.
7. Manually smoke-test:
   - `GET /healthz`
   - `GET /readyz`
   - published catalog browse
   - live search initial snapshot
   - live-search session refresh after enrichment

## Deploy Checklist

1. Deploy backend code and dependencies.
2. Apply migrations before routing traffic.
3. Confirm `GET /readyz` returns `200`.
4. Confirm TomTom-backed live search succeeds with the target environment key.
5. Confirm frontend is pointed at the intended API base URL.

## Rollback Checklist

1. Revert application code to the previous known-good build.
2. If a migration is backward-compatible, leave it in place and roll back only the app.
3. If a migration is not backward-compatible, stop and require a planned rollback path before deploying it.
4. Verify `GET /healthz` and `GET /readyz` after rollback.
5. Re-run a live-search smoke test.

## First Checks During an Incident

1. Check `GET /healthz` and `GET /readyz`.
2. Check HTTP metrics for rising 5xx counts or latency buckets.
3. Check live-search metrics for cache misses, enrichment failures, or write failures.
4. Check request logs for the affected path and request ID.
5. Distinguish between:
   - database readiness failure
   - TomTom upstream failure
   - Overpass enrichment failure
   - local storage failure for cache, sessions, or ops state
