from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from gymdb.application.jobs.receipt import JobReceipt
from gymdb.application.jobs.receipt_artifacts import maybe_write_fs_receipt
from gymdb.application.jobs.receipt_store import JobReceiptStoreDB


class IngestRunner:
    """
    Orchestrates a single ingest run against a durable receipt store.

    Responsibilities:
    - assign a stable job_id
    - persist the running → succeeded/failed lifecycle to Postgres
    - optionally write an FS receipt artifact (opt-in, non-authoritative)
    - surface failures via the returned receipt rather than raising

    The caller owns the receipt_store connection and transaction boundary.
    """

    @staticmethod
    def run(
        *,
        region: str,
        mode: str,
        ingest_fn: Callable[..., dict[str, Any]],
        receipt_store: JobReceiptStoreDB,
    ) -> JobReceipt:
        job_id = uuid.uuid4().hex
        started_at = datetime.now(UTC)

        running = JobReceipt.build(
            job_id=job_id,
            region=region,
            mode=mode,
            started_at=started_at,
            finished_at=None,
            status="running",
            stats={},
        )
        receipt_store.create(running)

        try:
            stats = ingest_fn(region=region)
            final_status = "succeeded"
        except Exception as exc:
            stats = {"error": str(exc)}
            final_status = "failed"

        finished_at = datetime.now(UTC)
        receipt_store.update_status(
            job_id=job_id,
            new_status=final_status,
            finished_at=finished_at,
            stats=stats,
        )

        final = JobReceipt.build(
            job_id=job_id,
            region=region,
            mode=mode,
            started_at=started_at,
            finished_at=finished_at,
            status=final_status,
            stats=stats,
            previous_status="running",
        )
        maybe_write_fs_receipt(final)
        return final
