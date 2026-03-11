def test_v2_review_coverage_contract(client, override_auth):
    resp = client.get("/v2/review/coverage?limit=1")
    assert resp.status_code == 200

    payload = resp.json()
    assert payload["api_version"] == "v2"
    assert "summary" in payload
    assert "results" in payload

    summary = payload["summary"]
    assert "matched" in summary
    assert "name_mismatch" in summary
    assert "unconfirmed" in summary
    assert "contradictions" in summary
    assert "low_confidence" in summary

    if payload["results"]:
        gym = payload["results"][0]
        assert "source_provenance" in gym
        assert "inference_meta" in gym


def test_v2_review_coverage_filters_by_status(client, override_auth):
    resp = client.get("/v2/review/coverage?status=matched&limit=10")
    assert resp.status_code == 200

    payload = resp.json()
    for gym in payload["results"]:
        assert gym["source_provenance"]["match_status"] == "matched"
