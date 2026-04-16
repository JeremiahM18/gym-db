# API Status

## Public API v2
Status: **FROZEN**

The `/v2` API is considered stable and safe for external client generation.

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
