from fastapi import APIRouter
from src.gymdb.observe.metrics import snapshot_metrics

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