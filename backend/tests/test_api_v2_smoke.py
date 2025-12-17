def test_v2_inference_has_confidence(client):
    data = client.get("/v2/gyms").json()
    inf = data["results"][0]["inference"]

    assert "confidence" in next(iter(inf.values()))