from fastapi import APIRouter, Query, HTTPException

from src.gymdb.domain import INFERRED, TIER_BASIC, TIER_MID, TIER_PREMIUM
from api.deps import registry, store
from src.gymdb.observe.summaries import summarize_inference
from src.gymdb.observe.metrics import record_inference_hits

router = APIRouter()

def _serialize_inference(gym: dict, include_reasons: bool) -> dict:
    """
    Serialize structured inference for API responses.
    """
    inferred = gym.get(INFERRED, {})

    if include_reasons:
        return inferred
    
    # Strip reasons, expose only values
    return {
        key: value["value"]
        for key, value in inferred.items()
        if isinstance(value, dict)
    }

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
    include_summary: bool = False,
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

    results = []
    for g in gyms:
        out = dict(g)
        out["inference"] = _serialize_inference(g, include_reasons)

        if include_summary:
            out["inference_summary"] = summarize_inference(g.get(INFERRED, {}))

        out.pop(INFERRED, None)
        results.append(out)

    return {
        "region": region,
        "count": len(results),
        "results": results,
}

@router.get("/gyms/{gym_id}")
def get_gym(
    gym_id: str, 
    region: str | None = None, 
    include_reasons: bool = False,
    include_summary: bool = False,
):
    region = region or registry.default_region

    gym = store.get_by_id(region, gym_id)
    if gym is None:
        raise HTTPException(status_code=404, detail="Gym not found")

    out = dict(gym)
    out["inference"] = _serialize_inference(gym, include_reasons)

    if include_summary:
        out["inference_summary"] = summarize_inference(gym.get(INFERRED, {}))

    record_inference_hits(g.get(INFERRED, {}))
    
    out.pop(INFERRED, None)
    return out