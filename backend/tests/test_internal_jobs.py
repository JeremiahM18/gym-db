from fastapi.testclient import TestClient
from api.main import app
from api.internal_routes.jobs import get_ingest_fn


def _admin_override():
    return {
        "sub": "admin-user",
        "cognito:groups": ["admin"],
    }

def fake_ingest(region: str):
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

    client = TestClient(app)
    resp = client.post("/internal/jobs/ingest")

    assert resp.status_code == 403

    app.dependency_overrides.clear()


def test_internal_jobs_ingest_admin_allowed(monkeypatch):
    """
    Admin users can trigger ingestion jobs
    """
    monkeypatch.setenv("ENABLE_INTERNAL", "true")

    from api.auth.dependencies import require_admin
    app.dependency_overrides[require_admin] = _admin_override

    app.dependency_overrides[get_ingest_fn] = lambda: fake_ingest
    
    client = TestClient(app)
    resp = client.post("/internal/jobs/ingest")

    assert resp.status_code == 200

    data = resp.json()
    assert "job_id" in data
    assert data["status"] in {"queued", "running", "succeeded"}

    app.dependency_overrides.clear()

def test_job_receipt_deterministic_hash_stable():
    from src.gymdb.jobs.receipt import JobReceipt
    from datetime import datetime, timezone

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
        stats={"b": 2, "a": 1},  # reordered
    )

    assert r1.deterministic_hash == r2.deterministic_hash

