from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy import create_engine, text

from gymdb.domain.processing import normalize_name
from gymdb.infrastructure.datasets.registry import DatasetRegistry
from gymdb.infrastructure.settings import settings
from gymdb.settings import BACKEND_ROOT

UPSERT_SQL = text(
    """
    INSERT INTO gyms (id, name, normalized_name, location)
    VALUES (
        :id,
        :name,
        :normalized_name,
        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
    )
    ON CONFLICT (id) DO UPDATE
    SET
        name = EXCLUDED.name,
        normalized_name = EXCLUDED.normalized_name,
        location = EXCLUDED.location
    """
)


def _load_dataset_results(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    results = payload.get("results") if isinstance(payload, dict) else payload
    if not isinstance(results, list):
        raise ValueError(f"Dataset at {path} must be a list or an object with results.")
    return [gym for gym in results if isinstance(gym, dict)]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync a published dataset into the canonical Postgres gyms table."
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=BACKEND_ROOT / "data/registry.json",
        help="Dataset registry to read.",
    )
    parser.add_argument(
        "--region",
        type=str,
        help="Region to sync. Defaults to the registry default region.",
    )
    args = parser.parse_args()

    registry = DatasetRegistry(args.registry).load()
    region = args.region or registry.default_region
    dataset_path = registry.dataset_path(region)
    gyms = _load_dataset_results(dataset_path)

    engine = create_engine(settings.postgres_dsn, future=True)
    synced = 0

    with engine.begin() as conn:
        for gym in gyms:
            gym_id = gym.get("id")
            name = gym.get("name")
            lat = gym.get("lat")
            lon = gym.get("lon")
            if not isinstance(gym_id, str) or not gym_id:
                continue
            if not isinstance(name, str) or not name:
                continue
            if not isinstance(lat, int | float) or not isinstance(lon, int | float):
                continue

            conn.execute(
                UPSERT_SQL,
                {
                    "id": gym_id,
                    "name": name,
                    "normalized_name": normalize_name(name),
                    "lat": float(lat),
                    "lon": float(lon),
                },
            )
            synced += 1

    engine.dispose()
    print(f"Synced {synced} gyms from {dataset_path.name} into Postgres.")


if __name__ == "__main__":
    main()
