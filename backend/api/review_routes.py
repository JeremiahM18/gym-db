from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from api.auth.dependencies import require_user
from api.deps import get_gym_store
from api.normalizers import serialize_gym, translate_store_error
from api.schemas_v2 import CoverageReviewResponseV2
from gymdb.gyms.protocol import GymStoreProtocol
from gymdb.gyms.review import list_review_gyms, summarize_review_gyms

router = APIRouter(
    prefix="/v2/review",
    tags=["review"],
    dependencies=[Depends(require_user)],
)


@router.get("/coverage", response_model=CoverageReviewResponseV2)
def coverage_review_v2(
    region: str | None = None,
    status: str | None = Query(None, pattern="^(matched|name_mismatch|unconfirmed)$"),
    max_conf: float | None = Query(None, ge=0.0, le=1.0),
    contradictions_only: bool = False,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    store: GymStoreProtocol = Depends(get_gym_store),
):
    region = region or store.default_region

    try:
        summary = summarize_review_gyms(store=store, region=region)
        gyms = list_review_gyms(
            store=store,
            region=region,
            status=status,
            max_conf=max_conf,
            contradictions_only=contradictions_only,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise translate_store_error(exc) from exc

    results = [serialize_gym(gym) for gym in gyms]
    return {
        "api_version": "v2",
        "region": region,
        "count": len(results),
        "has_more": len(results) == limit,
        "summary": summary,
        "results": results,
    }
