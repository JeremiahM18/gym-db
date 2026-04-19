# API Status

## Public API v2
Status: **FROZEN**

The `/v2` API is considered stable and safe for external client generation.
The public `/v2/gyms` route is the authoritative published-dataset browse surface, including nearby-style filtering through `lat`, `lon`, and `radius_m`.
The public `/v2/live/search` route is the live world search surface, backed by TomTom place resolution plus OpenStreetMap/Overpass live gym retrieval, with TomTom used for verification and enrichment.
The separate `/v2/gyms/geo/nearby` route is a lower-level PostGIS query surface and intentionally returns a slimmer distance-focused payload.

### Allowed Changes (No Version Bump)
- Adding new optional fields
- Adding new inference attributes
- Adding new optional query parameters
- Internal performance improvements

### Breaking Changes (Require v3)
- Removing fields
- Renaming fields
- Changing field types
- Changing semantic meaning of existing fields

Frontend clients may safely generate SDKs from the exported backend OpenAPI schema.
The checked-in `backend/openapi.json` snapshot is treated as part of the contract and is verified in CI against the live FastAPI app.
The checked-in frontend generated client is also verified in CI against that snapshot to prevent backend/frontend drift.
`has_more` on list responses is currently an approximate signal based on `len(results) == limit`, not an exact `limit + 1` pagination probe.
