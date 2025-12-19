def test_get_gym_v2_not_fount(client):
    resp = client.get("/v2/gyms/does-not-exist")
    assert resp.status_code == 404

def test_list_gyms_invalid_limit(client):
    resp = client.get("/v2/gyms?limit=10000")
    assert resp.status_code == 422