from api.auth.dependencies import require_admin
from api.settings import APISettings, get_settings


def _settings_with_internal(enabled: bool):
    return lambda: APISettings(enable_internal=enabled)


def test_internal_metrics_disabled_returns_404(client):
    resp = client.get("/internal/metrics/http")
    assert resp.status_code == 404


def test_internal_metrics_non_admin_forbidden(client, override_auth):
    client.app.dependency_overrides[get_settings] = _settings_with_internal(True)
    try:
        resp = client.get("/internal/metrics/http")
        assert resp.status_code == 403
    finally:
        client.app.dependency_overrides.pop(get_settings, None)


def test_internal_metrics_admin_allowed(client):
    admin_claims = {"sub": "admin", "cognito:groups": ["admin"]}
    client.app.dependency_overrides[get_settings] = _settings_with_internal(True)
    client.app.dependency_overrides[require_admin] = lambda: admin_claims

    try:
        resp = client.get("/internal/metrics/http")
        assert resp.status_code == 200
        assert "http" in resp.json()
    finally:
        client.app.dependency_overrides.pop(get_settings, None)
        client.app.dependency_overrides.pop(require_admin, None)
