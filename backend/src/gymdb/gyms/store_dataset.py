from __future__ import annotations

import json
from pathlib import Path


from src.gymdb.datasets.registry import DatasetRegistry


class DatasetGymStore:
    """
    Read-only store backed by static JSON datasets.

    Purpose:
    - Bootstrap ingestion
    - Offline processing
    - One-time data loads

    NOT USED by:
    - FastAPI routes
    -Runtime API requests

    Contract:
    - Deterministic reads from disk
    - No mutation / no writes
    - Region must resolve to a known dataset path
    """

    def __init__(self, registry: DatasetRegistry):
        self._registry = registry

    
    @property
    def default_region(self) -> str:
        return self._registry.default_region
    
    def _load_dataset(self, region: str) -> list[dict]:
        path = self._registry.dataset_path(region)

        if not path.exists():
            raise FileNotFoundError(
                f"Dataset not found for region `{region}`: {path}"
            )
        
        return json.loads(path.read_text(encoding="utf-8"))
    

    def filter(
            self,
            *,
            region: str,
            min_conf: float | None = None,
            limit: int = 100,
            offset: int = 0,
    ) -> list[dict]:
        gyms = self._load_dataset(region)

        if min_conf is not None:
            gyms = [
                g for g in gyms
                if g.get("confidence_score", 0.0) >= min_conf
            ]

        return gyms[offset : offset + limit]
    
    def get_by_id(self, region: str, gym_id: str) -> dict | None:
        gyms = self._load_dataset(region)

        for g in gyms:
            if g.get("id") == gym_id:
                return g
            
        return None
    
GymStore = DatasetGymStore