from __future__ import annotations

from gymdb.infrastructure.datasets.registry import DatasetRegistry
from gymdb.gyms.store_dataset import DatasetGymStore

from api.settings import APISettings


def create_registry(settings: APISettings) -> DatasetRegistry:
    """
    Construct and load the dataset registry.

    This is the ONLY place that:
    - touches registry paths
    - loads registry data
    """
    return DatasetRegistry(settings.registry_path).load()


def create_store(settings: APISettings) -> DatasetGymStore:
    """
    Construct the DatasetGymStore for the application.

    Store creation is centralized here so that:
    - deps.py stays simple
    - lifecycle ownership is explicit
    """
    registry = create_registry(settings)
    return DatasetGymStore(registry)

