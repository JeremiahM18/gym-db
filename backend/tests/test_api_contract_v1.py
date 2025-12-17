def test_api_version_present(client):
    resp = client.get("/v1/gyms")
    data = resp.json()

    assert data["api_version"] == "v1"
    assert "results" in data

def test_gym_schema_stability(client):
    gym = client.get("/v1/gyms").json()["results"][0]

    required = {
        "id", "name", "norm_name",
        "lat", "lon", "osm_refs",
        "tags", "inference"
    }
    
    assert required.issubset(gym.keys())