from __future__ import annotations

from typing import Iterable

from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from gymdb.infrastructure.db.db_models import GymNearby
from gymdb.infrastructure.db.errors import DatabaseUnavailable, QueryFailed


# --- SQL ---

SQL_NEARBY_GYMS = text("""
    SELECT
        g.id,
        g.name,
        ST_Y(g.location::geometry) AS lat,
        ST_X(g.location::geometry) AS lon,
        ST_Distance(
            g.location,
            ST_MakePoint(:lon, :lat)::geography
        ) AS distance_m
    FROM gyms g
    WHERE ST_DWithin(
        g.location,
        ST_MakePoint(:lon, :lat)::geography,
        :radius_m
    )
    ORDER BY distance_m ASC
    LIMIT :limit;
""")

SQL_DB_PING = text("SELECT 1 AS ok;")


# --- Helpers ---

def _execute_scalar(conn: Connection, sql) -> None:
    try:
        conn.execute(sql).scalar_one()
    except OperationalError as exc:
        raise DatabaseUnavailable("Database is unavailable") from exc
    except SQLAlchemyError as exc:
        raise QueryFailed("Database query failed") from exc


def _execute_query(
    conn: Connection,
    sql,
    params: dict,
) -> Iterable[dict]:
    try:
        return conn.execute(sql, params).mappings().all()
    except OperationalError as exc:
        raise DatabaseUnavailable("Database is unavailable") from exc
    except SQLAlchemyError as exc:
        raise QueryFailed("Database query failed") from exc


# --- Public API ---

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

    return [GymNearby.model_validate(row) for row in rows]

