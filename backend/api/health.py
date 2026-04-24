from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.engine import Connection

from api.deps import get_db
from api.readiness import (
    check_database,
    check_dataset_root,
    check_live_search_storage,
    check_ops_state_store,
    check_postgis,
    check_registry,
    check_schema,
)
from api.settings import APISettings, get_settings
from gymdb.domain.inference import RULESET_VERSION

router = APIRouter()
logger = logging.getLogger("gymdb")


@router.get("/healthz", tags=["health"])
def healthz(settings: APISettings = Depends(get_settings)):
    """
    Liveness probe.

    Confirms the service process is running.
    Does NOT check external dependencies.
    """
    return {
        "status": "ok",
        "api_version": "v2",
        "environment": settings.app_env,
    }


@router.get("/readyz", tags=["health"])
def readyz(
    db: Connection = Depends(get_db),
    settings: APISettings = Depends(get_settings),
):
    """
    Readiness probe.

    Confirms external dependencies (DB + extension + schema) are available.

    Returns 503 when NOT ready.

    503 responses are returned using the global error envelope:

    {
        "error": {
            "code": 503,
            "message": {
                "ready": false,
                "checks": {...}
            }
        }
    }
    """
    try:
        checks = {
            "database": check_database(db),
            "postgis": check_postgis(db),
            "schema": check_schema(db),
            "registry": check_registry(settings),
            "dataset_root": check_dataset_root(settings),
            "live_search_storage": check_live_search_storage(settings),
            "ops_state": check_ops_state_store(settings),
        }
    except Exception as exc:
        logger.exception("Readiness check failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "ready": False,
                "checks": {
                    "database": False,
                    "postgis": False,
                    "schema": False,
                    "registry": False,
                    "dataset_root": False,
                    "live_search_storage": False,
                    "ops_state": False,
                },
            },
        ) from exc

    ready = all(checks.values())

    payload = {
        "ready": ready,
        "checks": checks,
        "inference": {
            "engine": "rule_based",
            "version": RULESET_VERSION,
        },
        "environment": settings.app_env,
        "capabilities": {
            "live_search": {
                "configured": bool(settings.tomtom_api_key),
            }
        },
    }

    if not ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=payload,
        )

    return payload
