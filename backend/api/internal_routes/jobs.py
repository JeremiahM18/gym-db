from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status

from api.auth.internal import require_internal_enabled
from api.auth.dependencies import require_admin

from src.gymdb.jobs.store import JobStore
from src.gymdb.jobs.ingest_runner import IngestRunner
from src.gymdb.ingest import run_ingest

router = APIRouter(
    prefix="/internal/jobs",
    tags=["internal"],
    dependencies=[Depends(require_internal_enabled), Depends(require_admin)],
)

def get_job_store() -> JobStore:
    return JobStore(Path("data/jobs"))

def get_runner() -> IngestRunner:
    return IngestRunner(get_job_store())

@router.post("/ingest")
def start_ingest(region: str = "us"):
    runner = get_runner()
    job = runner.start(region=region, mode="manual")
    final = runner.run(
        job, 
        ingest_fn=lambda region: run_ingest(),
    )

    if final.status == "failed":
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=final.to_dict())

    return final.to_dict()

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
