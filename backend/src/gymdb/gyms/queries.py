from __future__ import annotations

from gymdb.gyms.protocol import GymStoreProtocol


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

    Filtering, pagination, and distance ordering are all delegated to the
    store. The store owns the query contract; this function is a thin
    dispatch layer with no filtering logic of its own.

    This is a PURE query function:
    - no filesystem access
    - no FastAPI imports
    - no global state
    """
    if lat is not None and lon is not None and radius_m is not None:
        return store.nearby(
            region=region,
            lat=lat,
            lon=lon,
            radius_m=radius_m,
            min_conf=min_conf,
            tier=tier,
            specialty=specialty,
            lifter_friendly=lifter_friendly,
            is_24_7=is_24_7,
            limit=limit,
            offset=offset,
        )
    return store.filter(
        region=region,
        min_conf=min_conf,
        tier=tier,
        specialty=specialty,
        lifter_friendly=lifter_friendly,
        is_24_7=is_24_7,
        limit=limit,
        offset=offset,
    )


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
