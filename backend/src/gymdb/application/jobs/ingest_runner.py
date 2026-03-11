from __future__ import annotations

import uuid
from dataclasses import replace

from .models import IngestJob, JobStatus, utc_now_iso
from .store import JobStore


def new_job_id() -> str:
    return uuid.uuid4().hex

class IngestRunner:
    def __init__(self, job_store: JobStore):
        self.job_store = job_store

    def start(self, *, region: str, mode: str) -> IngestJob:
        job = IngestJob(
            job_id=new_job_id(),
            kind="ingest",
            mode=mode,
            region=region,
            status=JobStatus.queued,
            created_at=utc_now_iso(),
            started_at=None,
            finished_at=None,
            metrics={},
            error=None,
        )
        self.job_store.save(job)
        return job

    def run(self, job: IngestJob, *, ingest_fn) -> IngestJob:
        running = replace(job, status=JobStatus.running, started_at=utc_now_iso())
        self.job_store.save(running)

        try:
            metrics = ingest_fn(region=running.region)  # must return dict metrics
            done = replace(
                running,
                status=JobStatus.succeeded,
                finished_at=utc_now_iso(),
                metrics=metrics or {},
            )
            self.job_store.save(done)
            return done
        except Exception as exc:
            failed = replace(
                running,
                status=JobStatus.failed,
                finished_at=utc_now_iso(),
                error=str(exc),
            )
            self.job_store.save(failed)
            return failed


