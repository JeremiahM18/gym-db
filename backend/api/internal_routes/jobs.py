from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone

from api.auth.internal import require_internal_enabled
from api.auth.dependencies import require_admin

from src.gymdb.jobs.store import JobStore
from src.gymdb.jobs.ingest_runner import IngestRunner
from src.gymdb.ingest import run_ingest
from src.gymdb.jobs.receipt import JobReceipt

router = APIRouter(
    prefix="/internal/jobs",
    tags=["internal"],
    dependencies=[Depends(require_internal_enabled), Depends(require_admin)],
)

def get_job_store() -> JobStore:
    return JobStore(Path("data/jobs"))

def get_runner() -> IngestRunner:
    return IngestRunner(get_job_store())

def get_ingest_fn():
    return run_ingest

@router.post("/ingest")
def start_ingest(
    region: str = "us",
    ingest_fn = Depends(get_ingest_fn),
):
    runner = get_runner()

    job = runner.start(region=region, mode="manual")
    started_at = datetime.now(timezone.utc)

    try:
        stats = ingest_fn(region)
        status_str = "succeeded"
        # result = runner.run(job, ingest_fn=ingest_fn)

        # # Normalize runner output
        # if isinstance(result, dict):
        #     stats = result
        # else:
        #     stats = {
        #         "gyms_fetched": result.gyms_fetched,
        #         "gyms_written": result.gyms_written,
        #         "deduped": result.deduped,
        #         "inferred": result.inferred,
        #     }
        # status_str = "succeeded"
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

    return receipt.to_dict()

@router.get("/{job_id}")
def get_job(job_id: str):
    store = get_job_store()
    try:
        return store.load(job_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")

@router.get("")
def list_jobs(limit: int = 25):
    store = get_job_store()
    return {"results": store.list_recent(limit=limit)}
