from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection, RowMapping
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from gymdb.infrastructure.db.db_models import GymNearby
from gymdb.infrastructure.db.errors import DatabaseUnavailable, QueryFailed

SQL_NEARBY_GYMS = text("""
    WITH anchor AS (
        SELECT
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) AS point_geometry,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography AS point_geography,
            degrees(:radius_m / 6371000.0) AS lat_delta,
            CASE
                WHEN abs(cos(radians(:lat))) < 1e-12 THEN 180.0
                ELSE degrees(:radius_m / 6371000.0) / abs(cos(radians(:lat)))
            END AS lon_delta
    ),
    candidates AS (
        SELECT
            g.id,
            g.name,
            g.location
        FROM gyms g
        CROSS JOIN anchor
        WHERE g.location::geometry && ST_MakeEnvelope(
            :lon - anchor.lon_delta,
            :lat - anchor.lat_delta,
            :lon + anchor.lon_delta,
            :lat + anchor.lat_delta,
            4326
        )
        ORDER BY g.location::geometry <-> anchor.point_geometry
        LIMIT GREATEST(:limit * 50, 500)
    )
    SELECT
        c.id,
        c.name,
        ST_Y(c.location::geometry) AS lat,
        ST_X(c.location::geometry) AS lon,
        ST_Distance(c.location, anchor.point_geography) AS distance_m
    FROM candidates c
    CROSS JOIN anchor
    WHERE ST_DWithin(
        c.location,
        anchor.point_geography,
        :radius_m
    )
    ORDER BY distance_m ASC
    LIMIT :limit;
""")

SQL_EXPLAIN_NEARBY_GYMS = text("""
    EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
    WITH anchor AS (
        SELECT
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) AS point_geometry,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography AS point_geography,
            degrees(:radius_m / 6371000.0) AS lat_delta,
            CASE
                WHEN abs(cos(radians(:lat))) < 1e-12 THEN 180.0
                ELSE degrees(:radius_m / 6371000.0) / abs(cos(radians(:lat)))
            END AS lon_delta
    ),
    candidates AS (
        SELECT
            g.id,
            g.name,
            g.location
        FROM gyms g
        CROSS JOIN anchor
        WHERE g.location::geometry && ST_MakeEnvelope(
            :lon - anchor.lon_delta,
            :lat - anchor.lat_delta,
            :lon + anchor.lon_delta,
            :lat + anchor.lat_delta,
            4326
        )
        ORDER BY g.location::geometry <-> anchor.point_geometry
        LIMIT GREATEST(:limit * 50, 500)
    )
    SELECT
        c.id,
        c.name,
        ST_Y(c.location::geometry) AS lat,
        ST_X(c.location::geometry) AS lon,
        ST_Distance(c.location, anchor.point_geography) AS distance_m
    FROM candidates c
    CROSS JOIN anchor
    WHERE ST_DWithin(
        c.location,
        anchor.point_geography,
        :radius_m
    )
    ORDER BY distance_m ASC
    LIMIT :limit;
""")

SQL_DB_PING = text("SELECT 1 AS ok;")


def _execute_scalar(conn: Connection, sql: Any) -> None:
    try:
        conn.execute(sql).scalar_one()
    except OperationalError as exc:
        raise DatabaseUnavailable("Database is unavailable") from exc
    except SQLAlchemyError as exc:
        raise QueryFailed("Database query failed") from exc


def _execute_query(
    conn: Connection,
    sql: Any,
    params: dict[str, Any],
) -> Sequence[RowMapping]:
    try:
        return conn.execute(sql, params).mappings().all()
    except OperationalError as exc:
        raise DatabaseUnavailable("Database is unavailable") from exc
    except SQLAlchemyError as exc:
        raise QueryFailed("Database query failed") from exc


def ping_db(conn: Connection) -> bool:
    """
    Lightweight DB liveness check.
    Intended for health probes.
    """
    _execute_scalar(conn, SQL_DB_PING)
    return True


def get_nearby_gyms(
    conn: Connection,
    *,
    lat: float,
    lon: float,
    radius_m: int,
    limit: int,
) -> list[GymNearby]:
    """
    Return nearby gyms ordered by exact geographic distance.

    The query first uses a conservative geometry bounding box plus KNN ordering
    to pull a small candidate set through the geometry expression index, then
    applies exact geography filtering and distance ordering on that reduced set.
    """
    rows = _execute_query(
        conn,
        SQL_NEARBY_GYMS,
        {
            "lat": lat,
            "lon": lon,
            "radius_m": radius_m,
            "limit": limit,
        },
    )

    return [GymNearby.model_validate(dict(row)) for row in rows]


def explain_nearby_gyms(
    conn: Connection,
    *,
    lat: float,
    lon: float,
    radius_m: int,
    limit: int,
) -> list[str]:
    """
    Return the textual EXPLAIN ANALYZE plan for the nearby query.
    """
    rows = _execute_query(
        conn,
        SQL_EXPLAIN_NEARBY_GYMS,
        {
            "lat": lat,
            "lon": lon,
            "radius_m": radius_m,
            "limit": limit,
        },
    )
    return [row["QUERY PLAN"] for row in rows]
