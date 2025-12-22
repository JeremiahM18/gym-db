-- Migration 001
-- Enable PostGIS and create the foundational gyms table
-- This migration establishes the irreversible spatial core of GymDB.

BEGIN;

-- Enable PostGIS (required for all geospatial operations)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Canonical gyms table
-- Represents physical gym locations in the real world
CREATE TABLE gyms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    location GEOGRAPHY(Point, 4326) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Prevent accidental deplicate canonical entries at identical locations
    UNIQUE (normalized_name, location)
);

-- Spatial index to support fast nearby and distance queries
CREATE INDEX gyms_location_gix
    ON gyms
    USING GIST (location);


-- Documentation
COMMENT ON TABLE gyms IS
'Canonical physical gym locations with geospatial indexing';

COMMIT;