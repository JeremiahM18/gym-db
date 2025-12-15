from pathlib import Path
import os

from api.registry import DatasetRegistry
from api.store import GymStore

REGISTRY_PATH = Path(os.getenv("GYMDB_REGISTRY", "data/registry.json"))

registry = DatasetRegistry(REGISTRY_PATH).load()
store = GymStore(registry)
