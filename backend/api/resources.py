from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from api.settings import APISettings
from gymdb.gyms.store_dataset import DatasetGymStore
from gymdb.infrastructure.datasets.registry import DatasetRegistry


@lru_cache(maxsize=8)
def _load_registry(registry_path: str) -> DatasetRegistry:
    return DatasetRegistry(Path(registry_path)).load()


@lru_cache(maxsize=8)
def _load_store(registry_path: str) -> DatasetGymStore:
    registry = _load_registry(registry_path)
    return DatasetGymStore(registry)


def create_registry(settings: APISettings) -> DatasetRegistry:
    """
    Construct and load the dataset registry.

    This is the ONLY place that:
    - touches registry paths
    - loads registry data
    """
    return _load_registry(str(settings.registry_path.resolve()))


def create_store(settings: APISettings) -> DatasetGymStore:
    """
    Construct the DatasetGymStore for the application.

    Store creation is centralized here so that:
    - deps.py stays simple
    - lifecycle ownership is explicit
    """
    return _load_store(str(settings.registry_path.resolve()))
