from fastapi.testclient import TestClient

from api.internal_routes.jobs import get_ingest_fn
from api.main import app


def _admin_override():
    return {
        "sub": "admin-user",
        "cognito:groups": ["admin"],
    }


def fake_ingest(*, region: str):
    return {
        "region": region,
        "gyms_fetched": 10,
        "gyms_written": 7,
        "deduped": 3,
        "inferred": 7,
    }


def test_internal_disabled_by_default():
    """
    Internal routes must NOT exist unless ENABLE_INTERNAL=true
    """
    client = TestClient(app)
    resp = client.post("/internal/jobs/ingest")
    assert resp.status_code == 404


def test_internal_requires_admin(monkeypatch):
    """
    ENABLE_INTERNAL=true but non-admin users are forbidden
    """
    monkeypatch.setenv("ENABLE_INTERNAL", "true")

    from api.auth.dependencies import require_user
    app.dependency_overrides[require_user] = lambda: {"sub": "user"}

    try:
        client = TestClient(app)
        resp = client.post("/internal/jobs/ingest")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.pop(require_user, None)
        monkeypatch.delenv("ENABLE_INTERNAL", raising=False)


def test_internal_jobs_ingest_admin_allowed(monkeypatch):
    """
    Admin users can trigger ingestion jobs
    """
    monkeypatch.setenv("ENABLE_INTERNAL", "true")

    from api.auth.dependencies import require_admin
    from api.internal_routes.jobs import get_receipt_store
    from tests.fake_receipt_store import FakeReceiptStore

    app.dependency_overrides[require_admin] = _admin_override
    app.dependency_overrides[get_ingest_fn] = lambda: fake_ingest
    app.dependency_overrides[get_receipt_store] = lambda: FakeReceiptStore()

    try:
        client = TestClient(app)
        resp = client.post("/internal/jobs/ingest")

        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        assert data["status"] == "succeeded"
    finally:
        app.dependency_overrides.pop(require_admin, None)
        app.dependency_overrides.pop(get_ingest_fn, None)
        app.dependency_overrides.pop(get_receipt_store, None)
        monkeypatch.delenv("ENABLE_INTERNAL", raising=False)


def test_job_receipt_deterministic_hash_stable():
    from datetime import datetime, timezone

    from gymdb.application.jobs.receipt import JobReceipt

    now = datetime(2025, 1, 1, tzinfo=timezone.utc)

    r1 = JobReceipt.build(
        job_id="job1",
        region="us",
        mode="manual",
        started_at=now,
        finished_at=now,
        status="succeeded",
        stats={"a": 1, "b": 2},
    )

    r2 = JobReceipt.build(
        job_id="job1",
        region="us",
        mode="manual",
        started_at=now,
        finished_at=now,
        status="succeeded",
        stats={"b": 2, "a": 1},
    )

    assert r1.deterministic_hash == r2.deterministic_hash


