# from fastapi.testclient import TestClient
# from api.main import app

# client = TestClient(app)

# def test_health_check():
#     response = client.get("/healthz")
#     assert response.status_code == 200
#     assert response.json() == {"status": "ok"}


# def test_list_regions():
#     resp = client.get("/v1/regions")
#     assert resp.status_code == 200

#     data = resp.json()
#     assert "default" in data
#     assert "regions" in data
#     assert isinstance(data["regions"], list)
#     assert len(data["regions"]) > 0

# def test_list_gyms_default_region():
#     resp = client.get("/v1/gyms")
#     assert resp.status_code == 200

#     data = resp.json()
#     assert "region" in data
#     assert "count" in data
#     assert "results" in data
#     assert isinstance(data["results"], list)

#     assert data["count"] == len(data["results"])

# def test_gym_has_stable_id():
#     resp = client.get("/v1/gyms")
#     gyms = resp.json()["results"]

#     assert len(gyms) > 0
#     assert "id" in gyms[0]
#     assert isinstance(gyms[0]["id"], str)
#     assert len(gyms[0]["id"]) > 0

# def test_get_gym_by_id_with_region():
#     resp = client.get("/v1/gyms")
#     data = resp.json()

#     region = data["region"]
#     gyms = data["results"]
#     gym_id = gyms[0]["id"]

#     resp = client.get(f"/v1/gyms/{gym_id}?region={region}")
#     assert resp.status_code == 200

#     gym = resp.json()
#     assert gym["id"] == gym_id
