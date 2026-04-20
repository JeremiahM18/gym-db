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


def test_list_gyms_has_more_is_false_at_exact_limit_boundary(client, override_auth):
    class ExactBoundaryStore:
        default_region = "nashville"

        def __init__(self):
            self.items = [
                {
                    "id": f"gym-{index}",
                    "name": f"Gym {index}",
                    "norm_name": f"gym_{index}",
                    "lat": 36.16 + index * 0.001,
                    "lon": -86.78,
                    "osm_refs": [{"type": "node", "id": index}],
                    "confidence_score": 0.9,
                    "inferred": {
                        "specialty": {
                            "value": "general_fitness",
                            "confidence": 0.8,
                            "reasons": ["test"],
                            "source": "rule",
                        }
                    },
                    "inference_meta": {
                        "engine": "rule_based",
                        "version": "1.1.0",
                        "generated_at": "2026-04-20T00:00:00Z",
                        "deterministic_hash": f"hash-{index}",
                        "field_confidence": {"specialty": 0.8},
                        "contradictions": {},
                    },
                    "source_provenance": {
                        "primary": "osm",
                        "confirmed_by": [],
                        "match_status": "matched",
                        "external_refs": {},
                    },
                }
                for index in range(2)
            ]

        def filter(self, *, limit, offset, **kwargs):
            return self.items[offset : offset + limit]

        def nearby(self, *, limit, offset, **kwargs):
            return self.filter(limit=limit, offset=offset, **kwargs)

        def get_by_id(self, region: str, gym_id: str):
            return next((item for item in self.items if item["id"] == gym_id), None)

    client.app.dependency_overrides[get_gym_store] = lambda: ExactBoundaryStore()
    try:
        resp = client.get("/v2/gyms?limit=2")
    finally:
        client.app.dependency_overrides.pop(get_gym_store, None)

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["count"] == 2
    assert payload["has_more"] is False


def test_list_gyms_has_more_is_true_when_extra_result_exists(client, override_auth):
    class OverflowStore:
        default_region = "nashville"

        def __init__(self):
            self.items = [
                {
                    "id": f"gym-{index}",
                    "name": f"Gym {index}",
                    "norm_name": f"gym_{index}",
                    "lat": 36.16 + index * 0.001,
                    "lon": -86.78,
                    "osm_refs": [{"type": "node", "id": index}],
                    "confidence_score": 0.9,
                    "inferred": {
                        "specialty": {
                            "value": "general_fitness",
                            "confidence": 0.8,
                            "reasons": ["test"],
                            "source": "rule",
                        }
                    },
                    "inference_meta": {
                        "engine": "rule_based",
                        "version": "1.1.0",
                        "generated_at": "2026-04-20T00:00:00Z",
                        "deterministic_hash": f"hash-{index}",
                        "field_confidence": {"specialty": 0.8},
                        "contradictions": {},
                    },
                    "source_provenance": {
                        "primary": "osm",
                        "confirmed_by": [],
                        "match_status": "matched",
                        "external_refs": {},
                    },
                }
                for index in range(3)
            ]

        def filter(self, *, limit, offset, **kwargs):
            return self.items[offset : offset + limit]

        def nearby(self, *, limit, offset, **kwargs):
            return self.filter(limit=limit, offset=offset, **kwargs)

        def get_by_id(self, region: str, gym_id: str):
            return next((item for item in self.items if item["id"] == gym_id), None)

    client.app.dependency_overrides[get_gym_store] = lambda: OverflowStore()
    try:
        resp = client.get("/v2/gyms?limit=2")
    finally:
        client.app.dependency_overrides.pop(get_gym_store, None)

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["count"] == 2
    assert payload["has_more"] is True
