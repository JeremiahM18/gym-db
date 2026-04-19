from tests.fakes import FakeDB


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_cors_allows_local_frontend_origin(client):
    resp = client.options(
        "/healthz",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "http://localhost:5173"

def test_readiness_success(client):
    from api.deps import get_db
    from api.settings import APISettings, get_settings

    # Override settings (what the route actually depends on)
    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        postgres_dsn="postgresql://test",
        aws_region="test",
        cognito_user_pool_id="test",
        cognito_app_client_id="test",
        cognito_issuer="https://example.com",
        enable_internal=True,
    )

    client.app.dependency_overrides[get_db] = lambda: FakeDB()

    resp = client.get("/readyz")
    assert resp.status_code == 200

    data = resp.json()
    assert data["ready"] is True
    assert data["checks"]["database"] is True
    assert data["checks"]["postgis"] is True
    assert data["checks"]["schema"] is True

    client.app.dependency_overrides.clear()


class BrokenDB:
    def execute(self, stmt):
        raise Exception("db down")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_readiness_failure(client):
    from api.deps import get_db
    from api.settings import APISettings, get_settings

    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        postgres_dsn="postgresql://test",
        aws_region="test",
        cognito_user_pool_id="test",
        cognito_app_client_id="test",
        cognito_issuer="https://example.com",
        enable_internal=True,
    )

    client.app.dependency_overrides[get_db] = lambda: BrokenDB()

    resp = client.get("/readyz")
    assert resp.status_code == 503

    error = resp.json()["error"]
    assert error["code"] == 503

    detail = error["message"]
    assert detail["ready"] is False
    assert detail["checks"]["database"] is False

    client.app.dependency_overrides.clear()
