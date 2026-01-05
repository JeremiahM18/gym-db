from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone

from api.auth.internal import require_internal_enabled
from api.auth.dependencies import require_admin

from src.gymdb.jobs.ingest_runner import IngestRunner
from src.gymdb.ingest import run_ingest
from src.gymdb.jobs.receipt import JobReceipt
from src.gymdb.jobs.receipt_store import JobReceiptStoreDB
from src.gymdb.jobs.receipt_artifacts import maybe_write_fs_receipt
from src.gymdb.jobs.queries import get_job_receipt, list_job_receipts


router = APIRouter(
    prefix="/internal/jobs",
    tags=["internal"],
    dependencies=[
        Depends(require_internal_enabled),
        Depends(require_admin)
    ],
)

# Dependencies

def get_runner() -> IngestRunner:
    from pathlib import Path
    from src.gymdb.jobs.store import JobStore

    return IngestRunner(JobStore(Path("data/jobs")))

def get_receipt_store() -> JobReceiptStoreDB:
    return JobReceiptStoreDB()

def get_ingest_fn():
    return run_ingest

# --- Routes ---

@router.post("/ingest")
def start_ingest(
    region: str = "us",
    ingest_fn = Depends(get_ingest_fn),
    receipt_store: JobReceiptStoreDB = Depends(get_receipt_store),
):
    """
    Trigger a manual ingest job and persist a deterministic job receipt.
    """
    runner = get_runner()
    job = runner.start(region=region, mode="manual")

    started_at = datetime.now(timezone.utc)

    # Create a receipt in "running" state

    running_receipt = JobReceipt.build(
        job_id=job.job_id,
        region=region,
        mode="manual",
        started_at=started_at,
        finished_at=None,
        status="running",
        stats={},   # stats are only know on completion
    )

    try:
        receipt_store.create(running_receipt)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job receipt: {exc}"
        )

    # Run ingest and determine terminal status

    try:
        stats = ingest_fn(region)
        final_status = "succeeded"
    except Exception as exc:
        stats = {}
        final_status = "failed"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(exc)
        )
    finally:
        finished_at = datetime.now(timezone.utc)

    # Transition job to terminal state + persist stats

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
            detail=f"Failed to finalize job receipt: {exc}"
        )
    
    # Best-effort FS artifact

    try:
        final_receipt = JobReceipt.build(
            job_id=job.job_id,
            region=region,
            mode="manual",
            started_at=started_at,
            finished_at=finished_at,
            status=final_status,
            stats=stats,
        )
        maybe_write_fs_receipt(final_receipt)
    except Exception:
        # Intentionally swallow: artifacts must never break persistence success
        pass

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
    except KeyError:
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
    return {
        "results": [r.to_dict() for r in receipts]
    }