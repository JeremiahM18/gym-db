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

router = APIRouter(
    prefix="/internal/jobs",
    tags=["internal"],
    dependencies=[Depends(require_internal_enabled), Depends(require_admin)],
)



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
    receipt_store = Depends(get_receipt_store),
):
    runner = get_runner()

    job = runner.start(region=region, mode="manual")
    started_at = datetime.now(timezone.utc)

    try:
        stats = ingest_fn(region)
        status_str = "succeeded"
    except Exception as exc:
        status_str = "failed"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(exc)
        )
    finally:
        finished_at = datetime.now(timezone.utc)

    receipt = JobReceipt.build(
        job_id=job.job_id,
        region=region,
        mode="manual",
        started_at=started_at,
        finished_at=finished_at,
        status=status_str,
        stats=stats,
    )

    try:
        receipt_store.save(receipt)
        maybe_write_fs_receipt(receipt)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save job receipt: {exc}"
        )

    return receipt.to_dict()

@router.get("/{job_id}")
def get_job(
    job_id: str,
    receipt_store = Depends(get_receipt_store),
):
    try:
        receipt = receipt_store.get(job_id)
        return receipt.to_dict()
    except KeyError:
        raise HTTPException(status_code=404, detail="Job receipt not found")
    

@router.get("")
def list_jobs(
    limit: int = 25,
    receipt_store = Depends(get_receipt_store),    
):
    receipts = receipt_store.list_recent(limit=limit)
    return {
        "results": [r.to_dict() for r in receipts]
    }