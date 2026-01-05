from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text


from api.auth.dependencies import require_admin
from api.auth.internal import require_internal_enabled
from src.gymdb.db.db_engine import get_connection
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

@router.get("/status")
def internal_status():
    """
    Internal system health and sanity check.
    Not part of the public API contract.
    """
    with get_connection() as db:
        # Database reachability
        try:
            db.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            db_ok = False

        # PostGIS check
        try:
            postgis = (
                db.execute(
                text("SELECT PostGIS_Version()"))
                .scalar() is not None
            )
        except Exception:
            postgis = False

        # Gym count
        try:
            gyms_count = (
                db.execute(
                text("SELECT COUNT(*) FROM gyms"))
                .scalar()
        )
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