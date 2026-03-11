def test_v2_gyms_response_contract(client):
    """
    Contract test for the public v2 gyms response.

    This test asserts the stable, documented resonse shape. 
    Auth is intentionally overridden to simulate a valid client.
    """

    # Auth override
    from api.auth.dependencies import require_user

    client.app.dependency_overrides[require_user] = lambda: None

    resp = client.get("/v2/gyms?limit=1")
    assert resp.status_code == 200

    payload = resp.json()

    # Top-level contract
    assert "results" in payload
    assert isinstance(payload["results"], list)

    if not payload["results"]:
        # Empty dataset is allowed; shape is still vaild
        return
    
    gym = payload["results"][0]

    # Core identity
    assert "id" in gym
    assert "name" in gym
    assert "lat" in gym
    assert "lon" in gym
    assert "osm_refs" in gym

    # Inference contract
    assert "inference" in gym
    assert isinstance(gym["inference"], dict)

    for key, value in gym["inference"].items():
        assert "value" in value
        assert "confidence" in value
        assert "reasons" in value

    # Inference metadata
    assert "inference_meta" in gym
    meta = gym["inference_meta"]
    assert "version" in meta
