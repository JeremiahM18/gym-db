from fastapi import APIRouter, Depends
from sqlalchemy import text

from api.deps import get_db
from api.auth.dependencies import require_admin
from api.auth.internal import require_internal_enabled
from src.gymdb.domain import INFERRED

router = APIRouter()

@router.get(
    "/status", 
    tags=["internal"], 
    dependencies=[ 
        Depends(require_internal_enabled), 
        Depends(require_admin),
        ],
)
def internal_status(db=Depends(get_db)):
    """
    Internal system health and sanity check.
    Not part of the public API contract.
    """
    # Database reachability
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # PostGIS check
    try:
        postgis = db.execute(
            text("SELECT PostGIS_Version()")
        ).scalar() is not None
    except Exception:
        postgis = False

    # Gym count
    try:
        gyms_count = db.execute(
            text("SELECT COUNT(*) FROM gyms")
        ).scalar()
    except Exception:
        gyms_count = None

    # Inference rules
    rules_loaded = len(INFERRED)

    return {
        "status": "ok" if db_ok else "degraded",
        "database": {
            "reachable": db_ok,
            "postgis_enabled": postgis,
            "gyms_count": gyms_count,
        },
        "inference": {
            "rules_loaded": rules_loaded
        },
    }