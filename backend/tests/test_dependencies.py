from fastapi.testclient import TestClient

from datetime import datetime, timezone
import hashlib

from api.main import app
from api.deps import get_store
from gymdb.infer.result import InferenceResult

class FakeStore:
    default_region = "test"

    def _gym(self):
        return {
            "id": "fake-gym",
            "name": "Fake Gym",
            "norm_name": "fake_gym",
            "lat": 0.0,
            "lon": 0.0,
            "osm_refs": [{"type": "node", "id": 1}],
            "confidence_score": 1.0,

            "inferred": {
                "is_24_7": InferenceResult(
                    value=True,
                    reasons=["fake text inference"],
                    confidence=1.0,
                    source="rule",
                )
            },

            "inference_meta": {
                "engine": "rule_based",
                "version": "0.0",
                "generated_at": datetime.now(timezone.utc),
                "deterministic_hash": hashlib.sha256(b"fake").hexdigest(),
            },
        }

    def filter(self, **kwargs):
        return[self._gym()]            
    
    def get_by_id(self, region: str, gym_id: str):
        if gym_id == "fake-gym":
            return self._gym()
        return None
    
def test_store_dependency_override():
    app.dependency_overrides[get_store] = lambda: FakeStore()

    client = TestClient(app)
    resp = client.get("/v2/gyms")

    assert resp.status_code == 200
    data = resp.json()
    assert data["results"][0]["id"] == "fake-gym"

    app.dependency_overrides.clear()