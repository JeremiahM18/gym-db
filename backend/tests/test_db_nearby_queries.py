from __future__ import annotations

from sqlalchemy import text

from gymdb.infrastructure.db.queries import explain_nearby_gyms, get_nearby_gyms

SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE TABLE IF NOT EXISTS gyms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    location GEOGRAPHY(Point, 4326) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (normalized_name, location)
);
CREATE INDEX IF NOT EXISTS gyms_location_gix
    ON gyms
    USING GIST (location);
CREATE INDEX IF NOT EXISTS gyms_location_geometry_gix
    ON gyms
    USING GIST ((location::geometry));
"""

INSERT_SQL = """
INSERT INTO gyms (id, name, normalized_name, location)
VALUES
    (
        'gym-near',
        'Near Gym',
        'near_gym',
        ST_SetSRID(ST_MakePoint(-86.7816, 36.1627), 4326)::geography
    ),
    (
        'gym-mid',
        'Mid Gym',
        'mid_gym',
        ST_SetSRID(ST_MakePoint(-86.7860, 36.1650), 4326)::geography
    ),
    (
        'gym-far',
        'Far Gym',
        'far_gym',
        ST_SetSRID(ST_MakePoint(-86.9000, 36.3000), 4326)::geography
    )
"""


def test_get_nearby_gyms_returns_ordered_results(db_session):
    conn = db_session.connection()
    for statement in filter(None, (part.strip() for part in SCHEMA_SQL.split(";"))):
        conn.execute(text(statement))

    conn.execute(text("TRUNCATE TABLE gyms"))
    conn.execute(text(INSERT_SQL))

    gyms = get_nearby_gyms(
        conn,
        lat=36.1627,
        lon=-86.7816,
        radius_m=1_000,
        limit=10,
    )

    assert [gym.id for gym in gyms] == ["gym-near", "gym-mid"]
    assert gyms[0].distance_m <= gyms[1].distance_m


def test_explain_nearby_gyms_returns_plan_lines(db_session):
    conn = db_session.connection()
    for statement in filter(None, (part.strip() for part in SCHEMA_SQL.split(";"))):
        conn.execute(text(statement))

    plan = explain_nearby_gyms(
        conn,
        lat=36.1627,
        lon=-86.7816,
        radius_m=1_000,
        limit=10,
    )

    assert plan
    assert any("Index" in line or "Scan" in line for line in plan)
