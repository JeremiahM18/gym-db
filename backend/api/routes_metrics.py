from fastapi import APIRouter

from gymdb.observe.metrics import snapshot_live_search_metrics, snapshot_metrics

router = APIRouter(tags=["metrics"])


@router.get(
    "/metrics/inference",
    include_in_schema=False,
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
    "/metrics/live-search",
    include_in_schema=False,
)
def live_search_metrics():
    """
    Lightweight observability endpoint.
    Reports cache probe, enrichment dispatch/outcome, and OSM confirmation tier
    distribution across all live-search requests since process start.
    """
    return {
        "live_search": snapshot_live_search_metrics(),
    }


