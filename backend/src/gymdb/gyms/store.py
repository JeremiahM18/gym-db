from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from src.gymdb.datasets.registry import DatasetRegistry


class GymStore:
    """
    Deterministic, read-only data access layer for gym datasets.

    Invariants:
    - Does NOT know about FastAPI
    - Does NOT know about auth
    - Does NOT apply inference or normalization
    - Only loads and filters raw gym records
    """

    def __init__(self, registry: DatasetRegistry):
        self._registry = registry

    
    @property
    def default_region(self) -> str:
        return self._registry.default_region
    
    def _load_dataset(self, region: str) -> list[dict]:
        path = self._registry.dataset_path(region)
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