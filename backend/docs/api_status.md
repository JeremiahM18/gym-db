# API Status

## Public API v2

Status: **stable**

The `/v2` API is the supported public surface. Changes are expected to preserve existing semantics unless a new version is introduced.

Operational endpoints such as `/healthz`, `/readyz`, and `/metrics/*` are intentionally outside this public contract.

## Public Routes

### Published catalog

- `GET /v2/gyms`
- `GET /v2/gyms/{gym_id}`
- `GET /v2/gyms/geo/nearby`
- `GET /v2/gyms/embeddings`

`/v2/gyms` is the primary published-dataset browse surface. `/v2/gyms/geo/nearby` is a narrower distance-first nearby endpoint.

### Geocoding

- `GET /v2/geocode`

TomTom-backed place lookup for the browser and other clients.

### Live search

- `GET /v2/live/search`
- `GET /v2/live/search/{search_id}`

`/v2/live/search` returns the initial live-search snapshot. Current behavior:

- TomTom resolves the place query
- TomTom supplies the initial nearby results
- GymDB deduplicates, scores, and annotates the snapshot
- fresh cached OSM confirmation may be applied immediately
- if enrichment is still pending, the response includes a `search_id` and session metadata

`/v2/live/search/{search_id}` returns the current state of that same live-search session. It exists so clients can refresh the same result set without reissuing the original TomTom search.

Current live-search response metadata includes:

- `search_id`
- `status`
- `enrichment_status`
- `revision`
- `updated_at`
- `expires_at`
- `poll_after_ms`

## Compatibility Rules

Allowed without a version bump:

- adding optional response fields
- adding optional query parameters
- adding new inference attributes
- internal performance or storage changes that preserve semantics

Require a version bump:

- removing fields
- renaming fields
- changing field types
- changing the semantic meaning of existing fields

## Contract Artifacts

- the checked-in OpenAPI snapshot is `backend/openapi.json`
- the checked-in frontend SDK is generated from that snapshot
- CI verifies that the FastAPI app still matches the snapshot
- CI also verifies that the frontend SDK still matches the checked-in snapshot

`has_more` on list responses is derived from an exact `limit + 1` probe, so clients can treat it as authoritative for pagination.
