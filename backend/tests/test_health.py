def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

# def test_readyz_shape(client):
#     resp = client.get("/readyz")
#     assert resp.status_code == 200
#     data = resp.json()

#     assert "status" in data
#     assert "db" in data
#     assert isinstance(data["db"], bool)

class FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value


class FakeDB:
    def execute(self, stmt):
        sql = str(stmt)

        if "SELECT 1" in sql:
            return FakeResult(1)

        if "PostGIS_Version" in sql:
            return FakeResult("3.4.0")

        if "COUNT" in sql:
            return FakeResult(123)

        return FakeResult(None)


def test_readiness_success(client):
    from api.deps import get_db

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

def test_readiness_failure(client):
    from api.deps import get_db

    client.app.dependency_overrides[get_db] = lambda: BrokenDB()

    resp = client.get("/readyz")
    assert resp.status_code == 503

    data = resp.json()["detail"]
    assert data["ready"] is False
    assert data["checks"]["database"] is False

    client.app.dependency_overrides.clear()

    