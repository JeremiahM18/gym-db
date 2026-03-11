-- Migration 002
-- Add an expression GIST index for geometry KNN ordering.
-- This keeps geography as the source of truth while enabling
-- index-assisted nearest-neighbor ordering for nearby queries.

BEGIN;

CREATE INDEX IF NOT EXISTS gyms_location_geometry_gix
    ON gyms
    USING GIST ((location::geometry));

COMMENT ON INDEX gyms_location_geometry_gix IS
'Expression index enabling KNN ordering on location::geometry for nearby queries';

COMMIT;
