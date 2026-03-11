from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gymdb.infrastructure.datasets.registry import DatasetRegistry


@dataclass(frozen=True)
class DatasetSnapshot:
    path: Path
    mtime_ns: int
    gyms: list[dict[str, Any]]
    by_id: dict[str, dict[str, Any]]


class DatasetGymStore:
    """
    Read-only store backed by published JSON dataset artifacts.

    Purpose:
    - Serve the read-only public API
    - Support offline inspection of deterministic read models
    - Keep published datasets separate from physical DB facts

    Contract:
    - Deterministic reads from disk
    - No mutation / no writes
    - Region must resolve to a known dataset path
    """

    def __init__(self, registry: DatasetRegistry):
        self._registry = registry
        self._cache: dict[str, DatasetSnapshot] = {}

    @property
    def default_region(self) -> str:
        return self._registry.default_region

    def _parse_dataset_payload(
        self,
        payload: Any,
        *,
        region: str,
        path: Path,
    ) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return payload

        if isinstance(payload, dict):
            results = payload.get("results")
            if isinstance(results, list):
                return results

        raise ValueError(
            "Dataset for region "
            f"`{region}` at {path} must be a list or an object "
            "with a results list"
        )

    def _load_dataset(self, region: str) -> DatasetSnapshot:
        path = self._registry.dataset_path(region)

        if not path.exists():
            raise FileNotFoundError(
                f"Dataset not found for region `{region}`: {path}"
            )

        mtime_ns = path.stat().st_mtime_ns
        cached = self._cache.get(region)
        if cached is not None and cached.path == path and cached.mtime_ns == mtime_ns:
            return cached

        payload = json.loads(path.read_text(encoding="utf-8"))
        gyms = self._parse_dataset_payload(payload, region=region, path=path)
        snapshot = DatasetSnapshot(
            path=path,
            mtime_ns=mtime_ns,
            gyms=gyms,
            by_id={gym["id"]: gym for gym in gyms if "id" in gym},
        )
        self._cache[region] = snapshot
        return snapshot

    def filter(
        self,
        *,
        region: str,
        min_conf: float | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        snapshot = self._load_dataset(region)
        gyms = snapshot.gyms

        if min_conf is not None:
            gyms = [
                gym for gym in gyms
                if gym.get("confidence_score", 0.0) >= min_conf
            ]

        return gyms[offset : offset + limit]

    def get_by_id(self, region: str, gym_id: str) -> dict[str, Any] | None:
        snapshot = self._load_dataset(region)
        return snapshot.by_id.get(gym_id)


GymStore = DatasetGymStore
