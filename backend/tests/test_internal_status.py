from api.main import app
from api.settings import APISettings, get_settings
from api.auth.dependencies import require_admin
from api.deps import get_db


class FakeResult:
    def __init__(self, scalar_value=None):
        self._scalar_value = scalar_value

    def scalar(self):
        return self._scalar_value

class FakeDB:
    def execute(self, stmt):
        sql = str(stmt)

        if "SELECT 1" in sql:
            return FakeResult(1)

        if "PostGIS_Version" in sql:
            return FakeResult("3.4.0")

        if "COUNT(*) FROM gyms" in sql:
            return FakeResult(123)

        return FakeResult(None)
    
    # allow usage in `with get_connection(...) as db`
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc, tb):
        return False

def test_internal_status(client, monkeypatch):
    # Enable internal routes
    monkeypatch.setenv("ENABLE_INTERNAL", "true")

    # Override admin auth
    from api.auth.dependencies import require_admin
    app.dependency_overrides[require_admin] = lambda: {
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

    app.dependency_overrides.clear()

