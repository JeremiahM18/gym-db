from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import ProgrammingError

from gymdb.infrastructure.db.queries import explain_nearby_gyms
from gymdb.infrastructure.settings import settings

CREATE_POSTGIS_SQL = "CREATE EXTENSION IF NOT EXISTS postgis"
SEED_SQL = """
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
TRUNCATE TABLE gyms;
INSERT INTO gyms (id, name, normalized_name, location)
SELECT
    'gym-' || i::text,
    'Gym ' || i::text,
    'gym_' || i::text,
    ST_SetSRID(
        ST_MakePoint(
            -86.95 + ((i % 500) * 0.0006),
            36.00 + ((i % 500) * 0.0006)
        ),
        4326
    )::geography
FROM generate_series(1, 20000) AS i;
ANALYZE gyms;
"""


def _run_sql_batch(conn: Connection, sql: str) -> None:
    for statement in filter(None, (part.strip() for part in sql.split(";"))):
        conn.execute(text(statement))


def _ensure_postgis(conn: Connection) -> bool:
    try:
        version = conn.execute(text("SELECT PostGIS_Version()")).scalar_one_or_none()
    except ProgrammingError:
        conn.rollback()
        version = None

    if version is not None:
        return True

    try:
        conn.execute(text(CREATE_POSTGIS_SQL))
        conn.commit()
    except ProgrammingError as exc:
        conn.rollback()
        print("PostGIS extension is not available and current user cannot create it.")
        print(
            "Provision the database with postgis/postgis or run migrations "
            "as a superuser."
        )
        print(f"Original error: {exc.orig}")
        return False

    return True


def main() -> None:
    print("GymDB PostGIS Query Plan")
    print(f"DSN: {settings.postgres_dsn}")

    from gymdb.infrastructure.db.db_engine import get_engine

    with get_engine().connect() as conn:
        if not _ensure_postgis(conn):
            return

        with conn.begin():
            _run_sql_batch(conn, SEED_SQL)
            plan = explain_nearby_gyms(
                conn,
                lat=36.1627,
                lon=-86.7816,
                radius_m=2_500,
                limit=25,
            )

    for line in plan:
        print(line)


if __name__ == "__main__":
    main()
