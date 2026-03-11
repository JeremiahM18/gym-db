from __future__ import annotations

from gymdb.domain.constants import (
    INFERRED,
    IS_24_7,
    LIFTER_FRIENDLY,
    SPECIALTY,
    TIER,
)
from gymdb.gyms.protocol import GymStoreProtocol


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


def list_gyms(
    *,
    store: GymStoreProtocol,
    region: str,
    min_conf: float | None = None,
    tier: str | None = None,
    specialty: str | None = None,
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
    if lat is not None and lon is not None and radius_m is not None:
        gyms = store.nearby(
            region=region,
            lat=lat,
            lon=lon,
            radius_m=radius_m,
            min_conf=min_conf,
        )
    else:
        gyms = store.filter(
            region=region,
            min_conf=min_conf,
            limit=10_000,
            offset=0,
        )

    if tier is not None:
        gyms = [g for g in gyms if _infer_value(g, TIER) == tier]

    if specialty is not None:
        gyms = [g for g in gyms if _infer_value(g, SPECIALTY) == specialty]

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
