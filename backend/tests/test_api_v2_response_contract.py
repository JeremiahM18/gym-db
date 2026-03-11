def test_v2_gyms_response_contract(client):
    """
    Contract test for the public v2 gyms response.

    This test asserts the stable, documented response shape.
    Auth is intentionally overridden to simulate a valid client.
    """

    from api.auth.dependencies import require_user

    client.app.dependency_overrides[require_user] = lambda: None

    resp = client.get("/v2/gyms?limit=1")
    assert resp.status_code == 200

    payload = resp.json()

    assert "results" in payload
    assert isinstance(payload["results"], list)

    if not payload["results"]:
        return

    gym = payload["results"][0]

    assert "id" in gym
    assert "name" in gym
    assert "lat" in gym
    assert "lon" in gym
    assert "osm_refs" in gym
    assert "norm_name" in gym
    assert gym["norm_name"]

    assert "inference" in gym
    assert isinstance(gym["inference"], dict)
    assert "specialty" in gym["inference"]

    for _key, value in gym["inference"].items():
        assert "value" in value
        assert "confidence" in value
        assert "reasons" in value

    assert "inference_meta" in gym
    meta = gym["inference_meta"]
    assert "version" in meta
    assert "field_confidence" in meta
    assert "contradictions" in meta

    assert "source_provenance" in gym
    provenance = gym["source_provenance"]
    assert "primary" in provenance
    assert "match_status" in provenance
    assert "external_refs" in provenance
