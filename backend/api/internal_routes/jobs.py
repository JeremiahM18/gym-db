from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.engine import Connection

from api.auth.dependencies import require_admin
from api.auth.internal import require_internal_enabled
from api.deps import get_db
from api.resources import create_registry
from api.settings import APISettings, get_settings
from gymdb.application.ingest import run_ingest_for_region
from gymdb.application.jobs.ingest_runner import IngestRunner
from gymdb.application.jobs.queries import get_job_receipt, list_job_receipts
from gymdb.application.jobs.receipt_store import JobReceiptNotFound, JobReceiptStoreDB
from gymdb.infrastructure.datasets.registry import DatasetRegistry

router = APIRouter(
    prefix="/internal/jobs",
    tags=["internal"],
    dependencies=[Depends(require_internal_enabled), Depends(require_admin)],
)


def get_receipt_store(
    db: Connection = Depends(get_db),
) -> JobReceiptStoreDB:
    return JobReceiptStoreDB(conn=db)


def get_registry(
    settings: APISettings = Depends(get_settings),
) -> DatasetRegistry:
    return create_registry(settings)


def get_ingest_fn(
    registry: DatasetRegistry = Depends(get_registry),
):
    def _ingest(*, region: str) -> dict:
        return run_ingest_for_region(registry=registry, region=region)

    return _ingest


@router.post("/ingest")
def start_ingest(
    region: str | None = Query(None),
    receipt_store: JobReceiptStoreDB = Depends(get_receipt_store),
    ingest_fn=Depends(get_ingest_fn),
    registry: DatasetRegistry = Depends(get_registry),
):
    """
    Trigger a manual ingest job and persist a deterministic job receipt.
    """
    target_region = region or registry.default_region

    try:
        receipt = IngestRunner.run(
            region=target_region,
            mode="manual",
            ingest_fn=ingest_fn,
            receipt_store=receipt_store,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    if receipt.status == "failed":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=receipt.stats.get("error", "Ingest failed"),
        )

    return {
        "job_id": receipt.job_id,
        "status": receipt.status,
    }


@router.get("/{job_id}")
def get_job(
    job_id: str,
    receipt_store: JobReceiptStoreDB = Depends(get_receipt_store),
):
    try:
        receipt = get_job_receipt(job_id, store=receipt_store)
        return receipt.to_dict()
    except (KeyError, JobReceiptNotFound) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job receipt not found",
        ) from exc


@router.get("/")
def list_jobs(
    limit: int = 25,
    receipt_store: JobReceiptStoreDB = Depends(get_receipt_store),
):
    receipts = list_job_receipts(limit=limit, store=receipt_store)
    return {"results": [r.to_dict() for r in receipts]}
