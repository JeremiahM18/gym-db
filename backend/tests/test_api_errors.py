from api.deps import get_gym_store


def test_get_gym_v2_not_fount(client, override_auth):
    resp = client.get("/v2/gyms/does-not-exist")
    assert resp.status_code == 404


def test_list_gyms_invalid_limit(client, override_auth):
    resp = client.get("/v2/gyms?limit=10000")
    assert resp.status_code == 422


def test_list_gyms_missing_dataset_returns_503(client, override_auth):
    class MissingDatasetStore:
        default_region = "nashville"

        def filter(self, **kwargs):
            raise FileNotFoundError("Dataset not found for region `nashville`")

        def nearby(self, **kwargs):
            raise FileNotFoundError("Dataset not found for region `nashville`")

        def get_by_id(self, region: str, gym_id: str):
            raise FileNotFoundError("Dataset not found for region `nashville`")

    client.app.dependency_overrides[get_gym_store] = lambda: MissingDatasetStore()
    try:
        resp = client.get("/v2/gyms")
    finally:
        client.app.dependency_overrides.pop(get_gym_store, None)

    assert resp.status_code == 503
    assert "Dataset not found" in resp.text
