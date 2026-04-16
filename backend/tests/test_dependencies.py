import hashlib
import json
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from api.auth.dependencies import require_user
from api.deps import get_gym_store
from api.main import app
from api.resources import create_store
from api.settings import APISettings
from gymdb.gyms.store_dataset import DatasetGymStore
from gymdb.infer.result import InferenceResult


class FakeGymStore(DatasetGymStore):
    default_region = "test"

    def __init__(self):
        pass

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
                "generated_at": datetime.now(UTC),
                "deterministic_hash": hashlib.sha256(b"fake").hexdigest(),
            },
        }

    def filter(self, **kwargs):
        return [self._gym()]

    def nearby(self, **kwargs):
        return self.filter(**kwargs)

    def get_by_id(self, region: str, gym_id: str):
        if gym_id == "fake-gym":
            return self._gym()
        return None


def _make_scratch_dir() -> Path:
    root = Path(".tmp") / f"dependency-store-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_store_dependency_override(override_auth):
    """
    Verify that GymStore dependency can be overridden for API tests.
    """
    app.dependency_overrides[get_gym_store] = lambda: FakeGymStore()

    client = TestClient(app)
    resp = client.get("/v2/gyms")

    assert resp.status_code == 200

    data = resp.json()
    assert data["results"][0]["id"] == "fake-gym"

    app.dependency_overrides.pop(require_user, None)


def test_create_store_reuses_cached_store_for_same_registry():
    root = _make_scratch_dir()
    try:
        registry_path = root / "registry.json"
        dataset_path = root / "gyms_test.json"

        dataset_path.write_text(json.dumps({"results": []}), encoding="utf-8")
        registry_path.write_text(
            json.dumps(
                {
                    "default": "test",
                    "datasets": {
                        "test": {
                            "file": dataset_path.name,
                            "lat": 0.0,
                            "lon": 0.0,
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

        settings = APISettings(
            registry_path=registry_path,
            dataset_root=root,
            postgres_dsn="postgresql+psycopg://test",
            aws_region="test",
            cognito_user_pool_id="test",
            cognito_app_client_id="test",
            cognito_issuer="https://example.com",
            enable_internal=False,
            enable_dev_auth_bypass=False,
        )

        first = create_store(settings)
        second = create_store(settings)

        assert first is second
    finally:
        shutil.rmtree(root, ignore_errors=True)
