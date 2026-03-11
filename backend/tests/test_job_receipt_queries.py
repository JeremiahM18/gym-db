from __future__ import annotations

from datetime import datetime, timezone

from gymdb.application.jobs.queries import get_job_receipt, list_job_receipts
from gymdb.application.jobs.receipt import JobReceipt
from gymdb.application.jobs.receipt_store import JobReceiptStoreDB
from gymdb.infrastructure.db.db_engine import get_engine


def test_queries_round_trip(db_session):
    with get_engine().begin() as conn:
        store = JobReceiptStoreDB(conn)
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


