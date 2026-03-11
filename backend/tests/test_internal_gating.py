def test_internal_disabled_returns_404(client):
    resp = client.get("/internal/status")
    assert resp.status_code == 404


def test_internal_enabled_non_admin_forbidden(client, monkeypatch, override_auth):
    monkeypatch.setenv("ENABLE_INTERNAL", "true")
    resp = client.get("/internal/status")
    assert resp.status_code == 403


def test_internal_enabled_admin_allowed(client, monkeypatch):
    monkeypatch.setenv("ENABLE_INTERNAL", "true")

    from api.auth.dependencies import require_admin
    from api.deps import get_db
    from api.main import app
    from tests.test_health import FakeDB

    admin_claims = {"sub": "admin", "cognito:groups": ["admin"]}
    app.dependency_overrides[require_admin] = lambda: admin_claims
    app.dependency_overrides[get_db] = lambda: FakeDB()

    resp = client.get("/internal/status")
    assert resp.status_code == 200

    app.dependency_overrides.clear()
