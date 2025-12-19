from __future__ import annotations

from fastapi import APIRouter

from src.gymdb.db.queries import ping_db
from src.gymdb.db.errors import DatabaseError

router = APIRouter()

@router.get("/healthz", tags=["health"])
def healthz():
    """
    Liveness probe.
    Confirms the service process is running.
    """
    return {"status": "ok"}

@router.get("/readyz", tags=["health"])
def readyz():
    """
    Readiness probe.
    Confirms external dependencies (DB) are available.
    """
    try:
        ping_db()
        return {
            "status": "ok",
            "db": True,
        }
    except DatabaseError:
        return {
            "status": "degraded",
             "db": False,
        }