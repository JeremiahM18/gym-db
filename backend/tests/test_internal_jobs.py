import uuid
from datetime import UTC
from pathlib import Path

from fastapi.testclient import TestClient

from api.internal_routes.jobs import get_ingest_fn, get_registry
from api.main import app
from api.settings import APISettings, get_settings
from gymdb.infrastructure.datasets.registry import DatasetRegistry


def _admin_override():
    return {
        "sub": "admin-user",
        "cognito:groups": ["admin"],
    }


def _settings_with_internal():
    return lambda: APISettings(enable_internal=True)


def _make_scratch_dir() -> Path:
    root = Path(".tmp") / f"internal-jobs-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def fake_ingest(*, region: str):
    return {
        "region": region,
        "gyms_fetched": 10,
        "gyms_written": 7,
        "deduped": 3,
        "inferred": 7,
    }


def test_internal_disabled_by_default():
    client = TestClient(app)
    resp = client.post("/internal/jobs/ingest")
    assert resp.status_code == 404


def test_internal_requires_admin():
    from api.auth.dependencies import require_user

    app.dependency_overrides[get_settings] = _settings_with_internal()
    app.dependency_overrides[require_user] = lambda: {"sub": "user"}

    try:
        client = TestClient(app)
        resp = client.post("/internal/jobs/ingest")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(require_user, None)


def test_internal_jobs_ingest_admin_allowed():
    from api.auth.dependencies import require_admin
    from api.internal_routes.jobs import get_receipt_store
    from tests.fake_receipt_store import FakeReceiptStore

    app.dependency_overrides[get_settings] = _settings_with_internal()
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
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(require_admin, None)
        app.dependency_overrides.pop(get_ingest_fn, None)
        app.dependency_overrides.pop(get_receipt_store, None)


def test_internal_jobs_use_registry_default_region():
    from api.auth.dependencies import require_admin
    from api.internal_routes.jobs import get_receipt_store
    from tests.fake_receipt_store import FakeReceiptStore

    root = _make_scratch_dir()
    registry_path = root / "registry.json"
    registry_path.write_text(
        '{"default":"custom-default","datasets":{"custom-default":{"file":"gyms.json","lat":0,"lon":0}}}',
        encoding="utf-8",
    )
    registry = DatasetRegistry(registry_path).load()

    seen: dict[str, str] = {}

    def capture_ingest(*, region: str):
        seen["region"] = region
        return {"region": region, "gyms_written": 0}

    app.dependency_overrides[get_settings] = _settings_with_internal()
    app.dependency_overrides[require_admin] = _admin_override
    app.dependency_overrides[get_registry] = lambda: registry
    app.dependency_overrides[get_ingest_fn] = lambda: capture_ingest
    app.dependency_overrides[get_receipt_store] = lambda: FakeReceiptStore()

    try:
        client = TestClient(app)
        resp = client.post("/internal/jobs/ingest")

        assert resp.status_code == 200
        assert seen["region"] == "custom-default"
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(require_admin, None)
        app.dependency_overrides.pop(get_registry, None)
        app.dependency_overrides.pop(get_ingest_fn, None)
        app.dependency_overrides.pop(get_receipt_store, None)


def test_job_receipt_deterministic_hash_stable():
    from datetime import datetime

    from gymdb.application.jobs.receipt import JobReceipt

    now = datetime(2025, 1, 1, tzinfo=UTC)

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
