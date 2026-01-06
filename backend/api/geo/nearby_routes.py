from __future__ import annotations

from fastapi import APIRouter, Query, Depends

from src.gymdb.db.queries import get_nearby_gyms
from src.gymdb.db.errors import DatabaseError

from api.deps import get_db, db_error_to_http
from api.schemas_v2 import GymsNearbyResponseV2, GymNearbyOutV2

router = APIRouter(prefix="/v2/gyms/geo", tags=["gyms"])

@router.get(
    "/nearby",
    response_model=GymsNearbyResponseV2,
)
def nearby_gyms(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_m: int = Query(1_000, ge=1, le=100_000),
    limit: int = Query(50, ge=1, le=100),
    db = Depends(get_db)
):
    """
    Find gyms near a geographic point.
    Uses PostGIS for distance calculations.
    """
    try:
        gyms = get_nearby_gyms(
            db,
            lat=lat,
            lon=lon,
            radius_m=radius_m,
            limit=limit,
        )
    except DatabaseError as exc:
        raise db_error_to_http(exc)
    
    api_results = [
        GymNearbyOutV2(
            id=g.id,
            name=g.name,
            lat=g.lat,
            lon=g.lon,
            distance_m=g.distance_m,
        )
        for g in gyms
    ]
    
    return {
        "api_version": "v2",
        "count": len(api_results),
        "results": api_results,
    }