import json
import shutil
import uuid
from pathlib import Path

from gymdb.application.ingest import run_ingest_for_region
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
