def test_v2_inference_has_confidence(client, override_auth):
    data = client.get("/v2/gyms").json()
    inf = data["results"][0]["inference"]

    assert "confidence" in next(iter(inf.values()))

def test_v2_requires_auth(client):
    resp = client.get("/v2/gyms")
    assert resp.status_code == 401
