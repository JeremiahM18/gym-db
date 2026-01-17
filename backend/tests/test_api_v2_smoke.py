from api.settings import APISettings, get_settings

def test_v2_inference_has_confidence(client, override_auth):
    data = client.get("/v2/gyms").json()
    inf = data["results"][0]["inference"]

    assert "confidence" in next(iter(inf.values()))

def test_v2_requires_auth(client):
    # Force auth bypass OFF for this test so it always validates the true security contract.
    client.app.dependency_overrides[get_settings] = lambda: APISettings(
        postgres_dsn="postgresql+psycopg://test",
        aws_region="test",
        cognito_user_pool_id="test",
        cognito_app_client_id="test",
        cognito_issuer="https://example.com",
        enable_internal=False,
        enable_dev_auth_bypass=False,       #Important
    )
    resp = client.get("/v2/gyms")
    assert resp.status_code == 401

    client.app.dependency_overrides.pop(get_settings, None)
