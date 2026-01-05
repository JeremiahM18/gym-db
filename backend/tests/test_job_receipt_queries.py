from __future__ import annotations

from datetime import datetime, timezone

from src.gymdb.jobs.queries import get_job_receipt, list_job_receipts
from src.gymdb.jobs.receipt import JobReceipt
from src.gymdb.jobs.receipt_store import JobReceiptStoreDB


def test_queries_round_trip(db_session):
    store = JobReceiptStoreDB()
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)

    receipt = JobReceipt.build(
        job_id="job_q_1",
        region="us",
        mode="manual",
        started_at=now,
        finished_at=now,
        status="succeeded",
        stats={"files_processed": 1},
    )

    store.create(receipt)

    loaded = get_job_receipt("job_q_1", store=store)
    assert loaded.job_id == "job_q_1"

    recent = list_job_receipts(limit=10, store=store)
    assert any(r.job_id == "job_q_1" for r in recent)