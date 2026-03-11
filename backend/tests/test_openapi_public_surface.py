def test_openapi_public_surface_is_clean(client):
    spec = client.get("/openapi.json").json()
    paths = spec["paths"].keys()

    for path in paths:
        assert not path.startswith("/internal")
        assert not path.startswith("/debug")
        assert not path.startswith("/metrics")
