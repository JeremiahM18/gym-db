import json
import os
from pathlib import Path
from typing import Any


class DatasetRegistry:
    def __init__(self, path: Path):
        self.path = path
        self._data: dict[str, Any] | None = None
        self._mtime_ns: int | None = None

    def load(self) -> "DatasetRegistry":
        if not self.path.exists():
            raise RuntimeError(f"Registry file not found at {self.path}.")

        self._data = json.loads(self.path.read_text(encoding="utf-8"))
        self._mtime_ns = self.path.stat().st_mtime_ns
        return self

    def _reload_if_stale(self) -> None:
        if not self.path.exists():
            if self._data is None:
                raise RuntimeError(f"Registry file not found at {self.path}.")
            raise RuntimeError(f"Registry file was removed from {self.path}.")

        current_mtime_ns = self.path.stat().st_mtime_ns
        if self._data is None or self._mtime_ns != current_mtime_ns:
            self._data = json.loads(self.path.read_text(encoding="utf-8"))
            self._mtime_ns = current_mtime_ns

    def _require_data(self) -> dict[str, Any]:
        self._reload_if_stale()
        if self._data is None:
            raise RuntimeError("Dataset registry must be loaded before use.")
        return self._data

    def _write(self) -> None:
        if self._data is None:
            raise RuntimeError(
                "Dataset registry must be loaded before it can be written."
            )

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2) + "\n", encoding="utf-8")
        self._mtime_ns = self.path.stat().st_mtime_ns

    def _normalize_dataset_file(self, file: str | Path) -> str:
        file_path = Path(file)
        resolved_file = (
            file_path.resolve()
            if file_path.is_absolute()
            else (Path.cwd() / file_path).resolve()
        )
        registry_root = self.path.parent.resolve()
        return os.path.relpath(resolved_file, start=registry_root).replace("\\", "/")

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

    def upsert_region(
        self,
        *,
        region: str,
        file: str | Path,
        lat: float,
        lon: float,
        radius_miles: float | None = None,
        place_label: str | None = None,
        set_default: bool = False,
    ) -> None:
        if self._data is None:
            if self.path.exists():
                self.load()
            else:
                self._data = {"default": region, "datasets": {}}
                self._mtime_ns = None

        data = self._data
        if data is None:
            raise RuntimeError("Dataset registry must be loaded before use.")
        datasets = data.setdefault("datasets", {})
        entry: dict[str, Any] = {
            "file": self._normalize_dataset_file(file),
            "lat": lat,
            "lon": lon,
        }
        if radius_miles is not None:
            entry["radius_miles"] = radius_miles
        if place_label:
            entry["place_label"] = place_label

        datasets[region] = entry

        if set_default or "default" not in data:
            data["default"] = region

        self._write()
