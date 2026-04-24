import logging

from api.auth.dependencies import require_user
from api.deps import get_db
from api.main import app
from api.settings import APISettings, get_settings
from tests.fakes import FakeDB


def test_internal_status(client, monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger="gymdb.audit")
    # Enable internal routes
    monkeypatch.setenv("ENABLE_INTERNAL", "true")

    # Override user auth so require_admin still runs and emits audit logs.
    app.dependency_overrides[require_user] = lambda: {
        "sub": "admin",
        "cognito:groups": ["admin"],
    }

    # Override settings so DB DSN is irrelevant
    app.dependency_overrides[get_settings] = lambda: APISettings(
        aws_region="us-east-1",
        cognito_user_pool_id="test",
        cognito_app_client_id="test",
        cognito_issuer="https://example.com",
        enable_internal=True,
    )

    app.dependency_overrides[get_db] = lambda: FakeDB()

    resp = client.get("/internal/status")
    assert resp.status_code == 200

    data = resp.json()
    assert "status" in data
    assert "database" in data
    assert "inference" in data
    assert data["database"]["reachable"] is True
    assert any(
        record.message == "admin_route_access"
        and getattr(record, "path", "") == "/internal/status"
        and getattr(record, "sub", "") == "admin"
        for record in caplog.records
    )

    app.dependency_overrides.clear()

