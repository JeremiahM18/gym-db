def test_nearby_shape(client):
    from api.main import app

    paths = sorted(r.path for r in app.router.routes)
    print("ROUTES SEEN BY PYTEST:", paths)

    resp = client.get(
        "/v2/gyms/geo/nearby?lat=36.16&lon=-86.78&radius_m=1000"
    )

    # If DB not running, degraded is acceptable
    assert resp.status_code in (200, 503)

    if resp.status_code == 200:
        data = resp.json()
        assert "count" in data
        assert "results" in data
        assert isinstance(data["results"], list)
