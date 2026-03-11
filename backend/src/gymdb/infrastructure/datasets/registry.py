import json
from pathlib import Path
from typing import Any


class DatasetRegistry:
    def __init__(self, path: Path):
        self.path = path
        self._data: dict[str, Any] | None = None

    def load(self) -> "DatasetRegistry":
        if not self.path.exists():
            raise RuntimeError(f"Registry file not found at {self.path}.")

        self._data = json.loads(self.path.read_text(encoding="utf-8"))
        return self

    def _require_data(self) -> dict[str, Any]:
        if self._data is None:
            raise RuntimeError("Dataset registry must be loaded before use.")
        return self._data

    @property
    def default_region(self) -> str:
        return self._require_data()["default"]

    def region_metadata(self, region: str) -> dict[str, Any]:
        datasets = self._require_data()["datasets"]
        if region not in datasets:
            raise KeyError(f"Unknown region: '{region}'")
        return datasets[region]

    def regions(self) -> list[str]:
        return list(self._require_data()["datasets"].keys())

    def dataset_path(self, region: str) -> Path:
        datasets = self._require_data()["datasets"]
        if region not in datasets:
            raise KeyError(f"Unknown region: '{region}'")

        base_dir = self.path.parent
        return base_dir / datasets[region]["file"]
