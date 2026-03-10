def test_job_receipt_round_trip(db_session):
    from gymdb.jobs.receipt_store import JobReceiptStoreDB
    from gymdb.jobs.receipt import JobReceipt
    from datetime import datetime, timezone
    from gymdb.db.db_engine import get_engine

    with get_engine().begin() as conn:

        store = JobReceiptStoreDB(conn)
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)

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


