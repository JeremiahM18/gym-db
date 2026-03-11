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
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography AS point_geography
    )
    SELECT
        g.id,
        g.name,
        ST_Y(g.location::geometry) AS lat,
        ST_X(g.location::geometry) AS lon,
        ST_Distance(g.location, anchor.point_geography) AS distance_m
    FROM gyms g
    CROSS JOIN anchor
    WHERE ST_DWithin(
        g.location,
        anchor.point_geography,
        :radius_m
    )
    ORDER BY g.location::geometry <-> anchor.point_geometry
    LIMIT :limit;
""")

SQL_EXPLAIN_NEARBY_GYMS = text("""
    EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
    WITH anchor AS (
        SELECT
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) AS point_geometry,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography AS point_geography
    )
    SELECT
        g.id,
        g.name,
        ST_Y(g.location::geometry) AS lat,
        ST_X(g.location::geometry) AS lon,
        ST_Distance(g.location, anchor.point_geography) AS distance_m
    FROM gyms g
    CROSS JOIN anchor
    WHERE ST_DWithin(
        g.location,
        anchor.point_geography,
        :radius_m
    )
    ORDER BY g.location::geometry <-> anchor.point_geometry
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
    Return nearby gyms ordered by distance.

    The query uses an exact geography radius filter and a geometry KNN order,
    which lets PostGIS use the geometry expression index for fast nearest-neighbor
    candidate ordering while still returning exact geographic distance.
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
