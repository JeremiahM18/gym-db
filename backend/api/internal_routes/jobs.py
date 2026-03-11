from __future__ import annotations

from datetime import datetime, timezone

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
from gymdb.application.jobs.receipt import JobReceipt
from gymdb.application.jobs.receipt_artifacts import maybe_write_fs_receipt
from gymdb.application.jobs.receipt_store import JobReceiptNotFound, JobReceiptStoreDB
from gymdb.application.jobs.store import JobStore
from gymdb.infrastructure.storage import JOBS_ROOT, ensure_storage_tree


router = APIRouter(
    prefix="/internal/jobs",
    tags=["internal"],
    dependencies=[Depends(require_internal_enabled), Depends(require_admin)],
)


def get_runner() -> IngestRunner:
    ensure_storage_tree()
    return IngestRunner(JobStore(JOBS_ROOT))


def get_receipt_store(
    db: Connection = Depends(get_db),
) -> JobReceiptStoreDB:
    """
    Construct a JobReceiptStore bound to the request-scoped DB connection.
    """
    return JobReceiptStoreDB(conn=db)


def get_ingest_fn(
    settings: APISettings = Depends(get_settings),
):
    registry = create_registry(settings)

    def _ingest(*, region: str) -> dict:
        target_region = region or registry.default_region
        return run_ingest_for_region(registry=registry, region=target_region)

    return _ingest


@router.post("/ingest")
def start_ingest(
    region: str | None = Query(None),
    runner: IngestRunner = Depends(get_runner),
    ingest_fn=Depends(get_ingest_fn),
    receipt_store: JobReceiptStoreDB = Depends(get_receipt_store),
):
    """
    Trigger a manual ingest job and persist a deterministic job receipt.
    """
    target_region = region or "nashville"
    job = runner.start(region=target_region, mode="manual")

    started_at = datetime.now(timezone.utc)

    running_receipt = JobReceipt.build(
        job_id=job.job_id,
        region=target_region,
        mode="manual",
        started_at=started_at,
        finished_at=None,
        status="running",
        stats={},
    )

    try:
        receipt_store.create(running_receipt)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job receipt: {exc}",
        )

    failure: Exception | None = None

    try:
        stats = ingest_fn(region=target_region)
        final_status = "succeeded"
    except Exception as exc:
        stats = {}
        final_status = "failed"
        failure = exc
    finally:
        finished_at = datetime.now(timezone.utc)

    try:
        receipt_store.update_status(
            job_id=job.job_id,
            new_status=final_status,
            finished_at=finished_at,
            stats=stats,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to finalize job receipt: {exc}",
        )

    try:
        final_receipt = JobReceipt.build(
            job_id=job.job_id,
            region=target_region,
            mode="manual",
            started_at=started_at,
            finished_at=finished_at,
            status=final_status,
            stats=stats,
            previous_status="running",
        )
        maybe_write_fs_receipt(final_receipt)
    except Exception:
        pass

    if failure is not None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(failure),
        )

    return {
        "job_id": job.job_id,
        "status": final_status,
    }


@router.get("/{job_id}")
def get_job(
    job_id: str,
    receipt_store: JobReceiptStoreDB = Depends(get_receipt_store),
):
    try:
        receipt = get_job_receipt(job_id, store=receipt_store)
        return receipt.to_dict()
    except (KeyError, JobReceiptNotFound):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job receipt not found",
        )


@router.get("/")
def list_jobs(
    limit: int = 25,
    receipt_store: JobReceiptStoreDB = Depends(get_receipt_store),
):
    receipts = list_job_receipts(limit=limit, store=receipt_store)
    return {"results": [r.to_dict() for r in receipts]}

