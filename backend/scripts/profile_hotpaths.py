from __future__ import annotations

import json
import random
import statistics
import time
from pathlib import Path

from gymdb.domain.processing import deduplicate
from gymdb.gyms.queries import list_gyms
from gymdb.gyms.store_dataset import DatasetGymStore
from gymdb.infrastructure.datasets.registry import DatasetRegistry


def _timed_run(fn, runs: int = 5) -> tuple[float, float]:
    samples: list[float] = []
    for _ in range(runs):
        started = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - started)
    return statistics.mean(samples), min(samples)


def _make_dedup_elements(count: int = 20_000, clusters: int = 2_000) -> list[dict]:
    random.seed(0)
    elements: list[dict] = []
    for idx in range(count):
        cluster = idx % clusters
        base_lat = 36.0 + cluster * 0.00035
        base_lon = -86.0 - cluster * 0.00035
        lat = base_lat + random.uniform(-0.00008, 0.00008)
        lon = base_lon + random.uniform(-0.00008, 0.00008)
        elements.append(
            {
                "type": "node",
                "id": idx,
                "lat": lat,
                "lon": lon,
                "tags": {"name": f"Gym {cluster}"},
            }
        )
    return elements


def _build_store_fixture(root: Path, gym_count: int = 15_000) -> DatasetGymStore:
    root.mkdir(parents=True, exist_ok=True)
    registry_path = root / "registry.json"
    dataset_path = root / "gyms.json"

    registry_path.write_text(
        json.dumps(
            {
                "default": "profile",
                "datasets": {
                    "profile": {
                        "file": dataset_path.name,
                        "lat": 36.1627,
                        "lon": -86.7816,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    results = []
    for idx in range(gym_count):
        results.append(
            {
                "id": f"gym-{idx}",
                "name": f"Gym {idx}",
                "lat": 36.0 + ((idx % 400) * 0.0005),
                "lon": -86.0 - ((idx % 400) * 0.0005),
                "confidence_score": round((idx % 100) / 100.0, 2),
                "inferred": {
                    "tier": {"value": "premium" if idx % 10 == 0 else "basic"},
                    "is_24_7": {"value": idx % 7 == 0},
                    "lifter_friendly": {"value": idx % 5 == 0},
                },
            }
        )

    dataset_path.write_text(
        json.dumps({"schema_version": "1.2", "results": results}),
        encoding="utf-8",
    )

    registry = DatasetRegistry(registry_path).load()
    return DatasetGymStore(registry)


def profile_dedup() -> None:
    elements = _make_dedup_elements()
    mean_s, min_s = _timed_run(lambda: deduplicate(elements), runs=5)
    print("Deduplication")
    print(f"  elements: {len(elements):,}")
    print(f"  mean:     {mean_s * 1000:.2f} ms")
    print(f"  best:     {min_s * 1000:.2f} ms")


def profile_dataset_store() -> None:
    root = Path(".tmp") / "profile-hotpaths"
    store = _build_store_fixture(root)

    store.filter(region="profile")

    filter_mean, filter_best = _timed_run(
        lambda: store.filter(region="profile", min_conf=0.7, limit=200, offset=100),
        runs=20,
    )
    lookup_mean, lookup_best = _timed_run(
        lambda: store.get_by_id("profile", "gym-12499"),
        runs=500,
    )
    geo_mean, geo_best = _timed_run(
        lambda: list_gyms(
            store=store,
            region="profile",
            lat=36.1627,
            lon=-86.7816,
            radius_m=2_500,
            limit=200,
            offset=0,
        ),
        runs=20,
    )

    print("Dataset Store / Query Path")
    print("  gyms:      15,000")
    print(
        "  filter:    "
        f"{filter_mean * 1000:.2f} ms mean "
        f"({filter_best * 1000:.2f} ms best)"
    )
    print(
        "  by-id:     "
        f"{lookup_mean * 1000:.4f} ms mean "
        f"({lookup_best * 1000:.4f} ms best)"
    )
    print(
        "  geo query: "
        f"{geo_mean * 1000:.2f} ms mean "
        f"({geo_best * 1000:.2f} ms best)"
    )


if __name__ == "__main__":
    print("GymDB Hot Path Profile")
    profile_dedup()
    profile_dataset_store()
