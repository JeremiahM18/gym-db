# Live Search Contract

## Goal

Live search should feel immediate without repeating the expensive TomTom lookup.

The contract is:

1. return an initial TomTom-backed snapshot quickly
2. enrich that same result set in place when OSM work finishes
3. let the client poll the saved search session instead of rerunning the original search

## Request Flow

### `GET /v2/live/search`

This creates a new live-search session and returns:

- the initial result snapshot
- a `search_id`
- session metadata for client refresh behavior

The initial snapshot always comes from:

- TomTom place resolution
- TomTom nearby gym search
- GymDB dedupe, scoring, and inference

Fresh cached OSM data may be applied immediately before the first response.

### `GET /v2/live/search/{search_id}`

This returns the current state of the same search session for the same authenticated user.

Clients should use this route to refresh a live-search result set that is already on screen.

## Status Fields

### `status`

- `enriching`
  - the initial snapshot is available
  - background OSM work may still change provenance, confidence, and metadata
  - clients should poll again after `poll_after_ms`
- `ready`
  - the current session state is final for the rest of the session lifetime
  - clients should stop polling

### `enrichment_status`

- `pending`
  - OSM follow-up is expected but has not completed yet
- `completed`
  - OSM enrichment finished and the saved session was updated
- `failed`
  - the initial search succeeded, but the OSM follow-up did not complete
- `skipped`
  - no background enrichment was needed because a fresh OSM cache was already applied

## Session Metadata

- `search_id`: stable identifier for the saved session
- `revision`: increments when the saved session is updated
- `updated_at`: when the current saved version was written
- `expires_at`: when the session should no longer be considered retrievable
- `poll_after_ms`: client poll hint; only meaningful while `status=enriching`

## Client UX Rules

The frontend should treat the result set as a single session, not as repeated searches.

Expected states:

1. Initial snapshot loaded
   - show results immediately
   - if `status=enriching`, show that refinement is still in progress

2. Enrichment completed
   - refresh the same visible results in place
   - preserve the user’s current selection when possible
   - stop polling

3. Enrichment failed
   - keep showing the TomTom-backed snapshot
   - stop polling
   - message this as a follow-up failure, not a search failure

4. Session expired or missing
   - treat the session as no longer refreshable
   - require a new live search instead of retrying the old session indefinitely

## What Can Change After Enrichment

The enriched response may change:

- `source_provenance.match_status`
- `source_provenance.confirmed_by`
- confidence score
- OSM-derived metadata such as hours, website, phone, operator, and address details

The enriched response must not trigger a second TomTom lookup for the same search session.
