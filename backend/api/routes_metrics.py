from fastapi import APIRouter, Depends

from api.auth.dependencies import require_admin
from api.auth.internal import require_internal_enabled
from gymdb.observe.metrics import (
    snapshot_http_metrics,
    snapshot_live_search_metrics,
    snapshot_metrics,
)

router = APIRouter(
    prefix="/internal/metrics",
    tags=["internal"],
    include_in_schema=False,
    dependencies=[Depends(require_internal_enabled), Depends(require_admin)],
)


@router.get(
    "/inference",
)
def inference_metrics():
    """
    Lightweight observability endpoint.
    Reports which inference rules have fired.
    """
    return {
        "inference_hits": snapshot_metrics(),
    }


@router.get(
    "/live-search",
)
def live_search_metrics():
    """
    Lightweight observability endpoint.
    Reports cache probe, enrichment dispatch/outcome, and OSM confirmation tier
    distribution recorded in the shared local ops-state store.
    """
    return {
        "live_search": snapshot_live_search_metrics(),
    }


@router.get(
    "/http",
)
def http_metrics():
    """Low-cardinality HTTP volume, error, and latency metrics."""
    return {
        "http": snapshot_http_metrics(),
    }
