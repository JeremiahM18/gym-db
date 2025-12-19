def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_readyz_shape(client):
    resp = client.get("/readyz")
    assert resp.status_code == 200
    data = resp.json()

    assert "status" in data
    assert "db" in data
    assert isinstance(data["db"], bool)