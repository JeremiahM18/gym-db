import json
import shutil
import uuid
from pathlib import Path

import pytest

from gymdb.application.ingest import TomTomPublishValidationError, run_ingest_for_region
from gymdb.infrastructure.datasets.read_model import (
    index_path_for_dataset,
    manifest_path_for_dataset,
)
from gymdb.infrastructure.datasets.registry import DatasetRegistry


def _make_scratch_dir() -> Path:
    root = Path(".tmp") / f"ingest-region-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_run_ingest_for_region_materializes_read_model(monkeypatch):
    root = _make_scratch_dir()
    try:
        dataset_path = root / "gyms_region.json"
        registry_path = root / "registry.json"
        registry_path.write_text(
            json.dumps(
                {
                    "default": "test",
                    "datasets": {
                        "test": {
                            "file": dataset_path.name,
                            "lat": 36.1627,
                            "lon": -86.7816,
                            "radius_miles": 5,
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        registry = DatasetRegistry(registry_path).load()

        monkeypatch.setattr(
            "gymdb.application.ingest.fetch_gyms",
            lambda radius_m, lat, lon: [],
        )

        metrics = run_ingest_for_region(registry=registry, region="test")

        materialized_dataset = Path(metrics["output_path"])
        materialized_read_model = Path(metrics["read_model_path"])
        manifest_path = manifest_path_for_dataset(materialized_dataset)

        assert materialized_dataset.exists()
        assert materialized_read_model.exists()
        assert manifest_path.exists()
        assert materialized_read_model == index_path_for_dataset(
            materialized_dataset,
            materialized_dataset.stat().st_mtime_ns,
        )

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["dataset_file"] == materialized_dataset.name
        assert manifest["read_model_file"] == materialized_read_model.name
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_run_ingest_for_region_writes_source_provenance(monkeypatch):
    root = _make_scratch_dir()
    try:
        dataset_path = root / "gyms_region.json"
        registry_path = root / "registry.json"
        registry_path.write_text(
            json.dumps(
                {
                    "default": "test",
                    "datasets": {
                        "test": {
                            "file": dataset_path.name,
                            "lat": 36.1627,
                            "lon": -86.7816,
                            "radius_miles": 5,
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        registry = DatasetRegistry(registry_path).load()

        monkeypatch.setattr(
            "gymdb.application.ingest.fetch_gyms",
            lambda radius_m, lat, lon: [
                {
                    "type": "node",
                    "id": 1,
                    "lat": 36.1627,
                    "lon": -86.7816,
                    "tags": {"name": "Life Time", "leisure": "fitness_centre"},
                }
            ],
        )
        monkeypatch.setattr(
            "gymdb.application.ingest.settings.tomtom_api_key", "test-key"
        )
        monkeypatch.setattr(
            "gymdb.application.ingest.TomTomClient.search_gyms",
            lambda self, lat, lon, radius_m, limit: [
                type(
                    "Place",
                    (),
                    {
                        "id": "tt-1",
                        "name": "Life Time",
                        "lat": 36.16271,
                        "lon": -86.78161,
                        "address": "Nashville, TN",
                        "city": "Nashville",
                        "country_code": "US",
                        "url": "https://www.lifetime.life/",
                        "raw": {},
                    },
                )()
            ],
        )

        metrics = run_ingest_for_region(registry=registry, region="test")
        payload = json.loads(Path(metrics["output_path"]).read_text(encoding="utf-8"))
        gym = payload["results"][0]

        assert metrics["coverage_matched"] == 1
        assert metrics["tomtom_validation_required"] is True
        assert metrics["tomtom_validation_applied"] is True
        assert gym["source_provenance"]["match_status"] == "matched"
        assert gym["source_provenance"]["confirmed_by"] == ["tomtom"]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_run_ingest_for_region_requires_tomtom_when_gyms_exist(monkeypatch):
    root = _make_scratch_dir()
    try:
        dataset_path = root / "gyms_region.json"
        registry_path = root / "registry.json"
        registry_path.write_text(
            json.dumps(
                {
                    "default": "test",
                    "datasets": {
                        "test": {
                            "file": dataset_path.name,
                            "lat": 36.1627,
                            "lon": -86.7816,
                            "radius_miles": 5,
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        registry = DatasetRegistry(registry_path).load()

        monkeypatch.setattr(
            "gymdb.application.ingest.fetch_gyms",
            lambda radius_m, lat, lon: [
                {
                    "type": "node",
                    "id": 1,
                    "lat": 36.1627,
                    "lon": -86.7816,
                    "tags": {"name": "Life Time", "leisure": "fitness_centre"},
                }
            ],
        )
        monkeypatch.setattr("gymdb.application.ingest.settings.tomtom_api_key", None)
        monkeypatch.setattr(
            "gymdb.application.ingest.settings.require_tomtom_publish_validation", True
        )

        with pytest.raises(TomTomPublishValidationError):
            run_ingest_for_region(registry=registry, region="test")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_run_ingest_for_region_can_opt_out_of_tomtom_gate_for_local_experiments(
    monkeypatch,
):
    root = _make_scratch_dir()
    try:
        dataset_path = root / "gyms_region.json"
        registry_path = root / "registry.json"
        registry_path.write_text(
            json.dumps(
                {
                    "default": "test",
                    "datasets": {
                        "test": {
                            "file": dataset_path.name,
                            "lat": 36.1627,
                            "lon": -86.7816,
                            "radius_miles": 5,
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        registry = DatasetRegistry(registry_path).load()

        monkeypatch.setattr(
            "gymdb.application.ingest.fetch_gyms",
            lambda radius_m, lat, lon: [
                {
                    "type": "node",
                    "id": 1,
                    "lat": 36.1627,
                    "lon": -86.7816,
                    "tags": {"name": "Life Time", "leisure": "fitness_centre"},
                }
            ],
        )
        monkeypatch.setattr("gymdb.application.ingest.settings.tomtom_api_key", None)

        metrics = run_ingest_for_region(
            registry=registry,
            region="test",
            require_tomtom_validation=False,
        )

        assert metrics["gyms_written"] == 1
        assert metrics["tomtom_validation_required"] is False
        assert metrics["tomtom_validation_applied"] is False
    finally:
        shutil.rmtree(root, ignore_errors=True)
