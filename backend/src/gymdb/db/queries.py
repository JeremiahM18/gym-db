from __future__ import annotations

from typing import Iterable

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from src.gymdb.db.db_engine import get_engine
from src.gymdb.db.errors import DatabaseUnavailable, QueryFailed
from src.gymdb.db.db_models import GymNearby

# --- SQL ---

SQL_NEARBY_GYMS = text("""
    SELECT 
        g.id,
        g.name,
        g.normalized_name,
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


# -- Helpers ---

def _execute_scalar(sql) -> None:
    engine = get_engine()
    try:
        with engine.begin() as conn:
            conn.execute(sql).scalar_one()
    except OperationalError as exc:
        raise DatabaseUnavailable("Database is unavailable") from exc
    except SQLAlchemyError as exc:
        raise QueryFailed("Database query failed") from exc
    

def _execute_query(sql, params: dict) -> Iterable[dict]:
    engine = get_engine()
    try:
        with engine.begin() as conn:
            return conn.execute(sql, params).mappings().all()
    except OperationalError as exc:
        raise DatabaseUnavailable("Database is unavailable") from exc
    except SQLAlchemyError as exc:
        raise QueryFailed("Database query failed") from exc
    

# --- Public API ---

def ping_db() ->bool:
    """
    Lightweight DB liveness check.
    Intended for health probes.
    """
    _execute_scalar(SQL_DB_PING)
    return True

def get_nearby_gyms(
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
        SQL_NEARBY_GYMS,
        {
            "lat": lat,
            "lon": lon,
            "radius_m": radius_m,
            "limit": limit,
        },
    )

    return [GymNearby.model_validate(row) for row in rows]