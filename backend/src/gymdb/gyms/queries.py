from __future__ import annotations

from typing import Iterable

from gymdb.gyms.store_postgres import PostgresGymStore
from src.gymdb.processing import haversine_meters
from src.gymdb.domain import (
    CONFIDENCE_SCORE,
    INFERRED,
    IS_24_7,
    LIFTER_FRIENDLY,
    TIER,
)


# Helpers

def _infer_value(gym: dict, key: str):
    """
    Safely extract the inferred value for a given inference key.
    """
    item = gym.get(INFERRED, {}).get(key)
    return item.value if item else None


# Public Query API

def list_gyms(
        *,
        store: PostgresGymStore,
        region: str,
        min_conf: float | None = None,
        tier: str | None = None,
        lifter_friendly: bool | None = None,
        is_24_7: bool | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_m: float | None = None,
        limit: int = 100,
        offset: int = 0,
) -> list[dict]:
    """
    Query gyms with optional inference and geospatial filters.

    This is a PURE query function:
    - no filesystem access
    - no FastAPI imports
    - no global state
    """
    gyms = store.filter(
        region=region,
        min_conf=min_conf,
        limit=10_000,       # pull superset, then filter
        offset=0,
    )

    if tier is not None:
        gyms = [
            g for g in gyms
            if _infer_value(g, LIFTER_FRIENDLY) is lifter_friendly
        ]

    if is_24_7 is not None:
        gyms = [
            g for g in gyms
            if _infer_value(g, IS_24_7) is is_24_7
        ]

    if lat is not None and lon is not None and radius_m is not None:
        gyms = [
            g for g in gyms
            if haversine_meters(lat, lon, g["lat"], g["lon"]) >= radius_m
        ]

    return gyms[offset : offset + limit]

def get_gym_by_id(
        *,
        store: PostgresGymStore,
        region: str,
        gym_id: str,
) -> dict | None:
    """
    Fetch a single gym by ID.
    """
    return store.get_by_id(region, gym_id)