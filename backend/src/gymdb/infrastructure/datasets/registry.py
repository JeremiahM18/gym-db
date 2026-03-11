import json
from pathlib import Path

class DatasetRegistry:
    def __init__(self, path: Path):
        self.path = path
        self._data = None

    def load(self) -> "DatasetRegistry":
        if not self.path.exists():
            raise RuntimeError(
                f"Registry file not found at {self.path}."
            )
        
        self._data = json.loads(self.path.read_text(encoding="utf-8"))
        return self
    
    @property
    def default_region(self) -> str:
        return self._data["default"]
    
    def region_metadata(self, region: str) -> dict:
        datasets = self._data["datasets"]
        if region not in datasets:
            raise KeyError(f"Unknown region: '{region}'")
        return datasets[region]
    
    def regions(self) -> list[str]:
        return list(self._data["datasets"].keys())
    
    def dataset_path(self, region: str) -> Path:
        datasets = self._data["datasets"]
        if region not in datasets:
            raise KeyError(f"Unknown region: '{region}'")
        
        base_dir = self.path.parent # directory containing registry.json
        return base_dir / datasets[region]["file"]

