from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy import Connection

from api.auth.dependencies import require_admin
from api.auth.internal import require_internal_enabled
from api.deps import get_db

from src.gymdb.domain import INFERRED

logger = logging.getLogger("gymdb")
router = APIRouter()



@router.get(
    "/status", 
    tags=["internal"], 
    dependencies=[ 
        Depends(require_internal_enabled), 
        Depends(require_admin),
        ],
)

#@router.get("/status")
def internal_status(db: Connection = Depends(get_db)):
    """
    Internal system health and sanity check.
    """

    db_ok = False
    postgis = False
    gyms_count = None

    try:
        db.execute(text("SELECT 1"))
        db_ok = True

        postgis = (
            db.execute(
            text("SELECT PostGIS_Version()"))
            .scalar() is not None
        )

        gyms_count = (
            db.execute(
            text("SELECT COUNT(*) FROM gyms"))
            .scalar()
        )
    except Exception:
            logger.exception("Internal status database checks failed")

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
    