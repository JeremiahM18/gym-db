from datetime import UTC


def test_job_receipt_round_trip(db_session):
    from datetime import datetime

    from gymdb.application.jobs.receipt import JobReceipt
    from gymdb.application.jobs.receipt_store import JobReceiptStoreDB
    from gymdb.infrastructure.db.db_engine import get_engine

    with get_engine().begin() as conn:
        store = JobReceiptStoreDB(conn)
        now = datetime(2025, 1, 1, tzinfo=UTC)

        receipt = JobReceipt.build(
            job_id="job_test_1",
            region="us",
            mode="manual",
            started_at=now,
            finished_at=now,
            status="succeeded",
            stats={"a": 1},
        )

        store.save(receipt)
        loaded = store.get("job_test_1")

        assert loaded.job_id == receipt.job_id
        assert loaded.region == receipt.region
        assert loaded.mode == receipt.mode
        assert loaded.status == receipt.status
        assert loaded.started_at == receipt.started_at
        assert loaded.finished_at == receipt.finished_at
        assert loaded.stats == receipt.stats
        assert loaded.deterministic_hash == receipt.deterministic_hash


def test_running_job_receipt_serializes_without_finished_at():
    from datetime import datetime

    from gymdb.application.jobs.receipt import JobReceipt

    now = datetime(2025, 1, 1, tzinfo=UTC)
    receipt = JobReceipt.build(
        job_id="job_running_1",
        region="us",
        mode="manual",
        started_at=now,
        finished_at=None,
        status="running",
        stats={},
    )

    payload = receipt.to_dict()

    assert payload["status"] == "running"
    assert payload["finished_at"] is None
