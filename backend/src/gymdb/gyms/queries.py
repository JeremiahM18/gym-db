from __future__ import annotations

import math

from gymdb.domain.constants import INFERRED, IS_24_7, LIFTER_FRIENDLY, TIER
from gymdb.domain.processing import haversine_meters
from gymdb.gyms.protocol import GymStoreProtocol

_EARTH_RADIUS_METERS = 6_371_000.0


def _infer_value(gym: dict, key: str):
    """
    Safely extract the inferred value for a given inference key.
    """
    item = gym.get(INFERRED, {}).get(key)
    if item is None:
        return None
    if hasattr(item, "value"):
        return item.value
    if isinstance(item, dict):
        return item.get("value")
    return None


def _bounding_box(
    lat: float,
    lon: float,
    radius_m: float,
) -> tuple[float, float, float, float]:
    lat_delta = math.degrees(radius_m / _EARTH_RADIUS_METERS)
    cos_lat = math.cos(math.radians(lat))
    lon_delta = 180.0 if abs(cos_lat) < 1e-12 else lat_delta / cos_lat
    return (
        lat - lat_delta,
        lat + lat_delta,
        lon - lon_delta,
        lon + lon_delta,
    )


def list_gyms(
    *,
    store: GymStoreProtocol,
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
        limit=10_000,
        offset=0,
    )

    if tier is not None:
        gyms = [g for g in gyms if _infer_value(g, TIER) == tier]

    if lifter_friendly is not None:
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
        min_lat, max_lat, min_lon, max_lon = _bounding_box(lat, lon, radius_m)
        gyms = [
            gym for gym in gyms
            if min_lat <= gym["lat"] <= max_lat
            and min_lon <= gym["lon"] <= max_lon
            and haversine_meters(lat, lon, gym["lat"], gym["lon"]) <= radius_m
        ]

    return gyms[offset : offset + limit]


def get_gym_by_id(
    *,
    store: GymStoreProtocol,
    region: str,
    gym_id: str,
) -> dict | None:
    """
    Fetch a single gym by ID.
    """
    return store.get_by_id(region, gym_id)
