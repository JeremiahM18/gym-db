import json
import shutil
import time
import uuid
from pathlib import Path

from gymdb.gyms.store_dataset import DatasetGymStore
from gymdb.infrastructure.datasets.registry import DatasetRegistry


def _make_scratch_dir() -> Path:
    root = Path(".tmp") / f"dataset-store-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _write_registry(
    root: Path,
    dataset_name: str = "gyms_test.json",
) -> DatasetRegistry:
    registry_path = root / "registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "default": "test",
                "datasets": {
                    "test": {
                        "file": dataset_name,
                        "lat": 0.0,
                        "lon": 0.0,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return DatasetRegistry(registry_path).load()


def test_dataset_store_reads_enveloped_results_payload():
    root = _make_scratch_dir()
    try:
        dataset_path = root / "gyms_test.json"
        dataset_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.2",
                    "results": [
                        {
                            "id": "gym-1",
                            "name": "Test Gym",
                            "confidence_score": 0.9,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        store = DatasetGymStore(_write_registry(root), cache_recheck_ns=0)

        results = store.filter(region="test", min_conf=0.8)

        assert [gym["id"] for gym in results] == ["gym-1"]
        assert store.get_by_id("test", "gym-1")["name"] == "Test Gym"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dataset_store_invalidates_cache_when_dataset_changes():
    root = _make_scratch_dir()
    try:
        dataset_path = root / "gyms_test.json"
        dataset_path.write_text(
            json.dumps({"results": [{"id": "gym-1", "name": "First"}]}),
            encoding="utf-8",
        )

        store = DatasetGymStore(_write_registry(root), cache_recheck_ns=0)

        first = store.get_by_id("test", "gym-1")
        assert first["name"] == "First"

        time.sleep(0.01)
        dataset_path.write_text(
            json.dumps({"results": [{"id": "gym-1", "name": "Updated"}]}),
            encoding="utf-8",
        )

        updated = store.get_by_id("test", "gym-1")
        assert updated["name"] == "Updated"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_dataset_store_nearby_uses_geo_indexed_candidates():
    root = _make_scratch_dir()
    try:
        dataset_path = root / "gyms_test.json"
        dataset_path.write_text(
            json.dumps(
                {
                    "results": [
                        {
                            "id": "nearby",
                            "name": "Near Gym",
                            "lat": 36.1627,
                            "lon": -86.7816,
                            "confidence_score": 0.9,
                        },
                        {
                            "id": "far",
                            "name": "Far Gym",
                            "lat": 36.3627,
                            "lon": -86.7816,
                            "confidence_score": 0.9,
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )

        store = DatasetGymStore(_write_registry(root), cache_recheck_ns=0)
        results = store.nearby(
            region="test",
            lat=36.1627,
            lon=-86.7816,
            radius_m=1_000,
            min_conf=0.5,
        )

        assert [gym["id"] for gym in results] == ["nearby"]
    finally:
        shutil.rmtree(root, ignore_errors=True)

