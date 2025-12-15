from fastapi import APIRouter, Query, HTTPException
from pathlib import Path
import os

from api.store import GymStore
from src.gymdb.domain import TIER_BASIC, TIER_MID, TIER_PREMIUM
from api.registry import DatasetRegistry


router = APIRouter()

# --- Configuration ---
REGISTRY_PATH = Path(
    os.getenv("GYMDB_REGISTRY", "data/registry.json")
)

# Load registry once
registry = DatasetRegistry(REGISTRY_PATH).load()
store = GymStore(registry)

# --- Routes ---

@router.get("/regions")
def list_regions():
    return {
        "default": registry.default_region,
        "regions": registry.regions(),
    }

@router.get("/gyms")
def list_gyms(
    region: str | None = None,
    min_conf: float | None = Query(None, ge=0.0, le=1.0),
    tier: str | None = Query(
        None, 
        description=f"{TIER_BASIC} | {TIER_MID} | {TIER_PREMIUM}"
    ),
    lifter_friendly: bool | None = None,
    is_24_7: bool | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_m: float | None = None,
    include_reasons: bool = False,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    region = region or registry.default_region

    gyms = store.filter(
        region=region,
        min_conf=min_conf,
        tier=tier,
        lifter_friendly=lifter_friendly,
        is_24_7=is_24_7,
        lat=lat,
        lon=lon,
        radius_m=radius_m,
        limit=limit,
        offset=offset,
    )

    if not include_reasons:
        for g in gyms:
            g.pop("inference_reasons", None)

    return {
        "region": region,
        "count": len(gyms),
        "results": gyms,
}

@router.get("/gyms/{gym_id}")
def get_gym(
    gym_id: str, 
    region: str | None = None, 
    include_reasons: bool = False
):
    region = region or registry.default_region

    gym = store.get_by_id(region, gym_id)
    if gym is None:
        raise HTTPException(status_code=404, detail="Gym not found")

    if not include_reasons:
        gym.pop("inference_reasons", None)

    return gym