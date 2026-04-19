import json
import time
from pathlib import Path

from gymdb.infrastructure.datasets.registry import DatasetRegistry


def test_registry_reloads_when_file_changes():
    root = Path(".tmp") / f"registry-reload-{time.time_ns()}"
    root.mkdir(parents=True, exist_ok=True)
    registry_path = root / "registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "default": "nashville",
                "datasets": {
                    "nashville": {
                        "file": "gyms_nashville.json",
                        "lat": 36.16,
                        "lon": -86.78,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    registry = DatasetRegistry(registry_path).load()
    assert registry.default_region == "nashville"

    time.sleep(0.01)
    registry_path.write_text(
        json.dumps(
            {
                "default": "franklin",
                "datasets": {
                    "franklin": {
                        "file": "gyms_franklin.json",
                        "lat": 35.92,
                        "lon": -86.87,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    assert registry.default_region == "franklin"
    assert registry.dataset_path("franklin").name == "gyms_franklin.json"


def test_registry_upsert_region_persists_new_place_metadata():
    root = Path(".tmp") / f"registry-upsert-{time.time_ns()}"
    root.mkdir(parents=True, exist_ok=True)
    registry_path = root / "registry.json"

    registry = DatasetRegistry(registry_path)
    registry.upsert_region(
        region="franklin_tn",
        file=root / "gyms_franklin_tn.json",
        lat=35.9236,
        lon=-86.8678,
        radius_miles=12.0,
        place_label="Franklin, TN",
        set_default=True,
    )

    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    assert payload["default"] == "franklin_tn"
    assert payload["datasets"]["franklin_tn"]["file"] == "gyms_franklin_tn.json"
    assert payload["datasets"]["franklin_tn"]["place_label"] == "Franklin, TN"
    assert payload["datasets"]["franklin_tn"]["radius_miles"] == 12.0
