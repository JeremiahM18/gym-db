from __future__ import annotations

import json
import os
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from gymdb.domain.inference import apply_inference
from gymdb.domain.models import Gym
from gymdb.domain.processing import haversine_meters
from gymdb.gyms.queries import list_gyms
from gymdb.gyms.store_dataset import DatasetGymStore
from gymdb.infrastructure.datasets.registry import DatasetRegistry

DATASET_SIZE = 20_000
QUERY_WORKERS = 16
QUERY_TASKS = 400
INFERENCE_WORKERS = 16
INFERENCE_TASKS = 4_000
QUERY_CENTER_LAT = 36.10
QUERY_CENTER_LON = -86.10
BROAD_QUERY_RADIUS_M = 20_000
FOCUSED_QUERY_RADIUS_M = 2_500


class NaiveDatasetGymStore:
    default_region = "profile"

    def __init__(self, gyms: tuple[dict[str, Any], ...]):
        self._gyms = gyms

    def _matches_filters(
        self,
        gym: dict[str, Any],
        *,
        min_conf: float | None,
        tier: str | None,
        specialty: str | None,
        lifter_friendly: bool | None,
        is_24_7: bool | None,
    ) -> bool:
        inferred = gym.get("inferred", {})
        if min_conf is not None and gym.get("confidence_score", 0.0) < min_conf:
            return False
        if tier is not None and inferred.get("tier", {}).get("value") != tier:
            return False
        if (
            specialty is not None
            and inferred.get("specialty", {}).get("value") != specialty
        ):
            return False
        if (
            lifter_friendly is not None
            and inferred.get("lifter_friendly", {}).get("value")
            is not lifter_friendly
        ):
            return False
        if (
            is_24_7 is not None
            and inferred.get("is_24_7", {}).get("value") is not is_24_7
        ):
            return False
        return True

    def filter(self, **kwargs) -> list[dict[str, Any]]:
        results = [
            gym
            for gym in self._gyms
            if self._matches_filters(
                gym,
                min_conf=kwargs.get("min_conf"),
                tier=kwargs.get("tier"),
                specialty=kwargs.get("specialty"),
                lifter_friendly=kwargs.get("lifter_friendly"),
                is_24_7=kwargs.get("is_24_7"),
            )
        ]
        offset = kwargs.get("offset", 0)
        limit = kwargs.get("limit", 100)
        return results[offset : offset + limit]

    def nearby(self, **kwargs) -> list[dict[str, Any]]:
        lat = kwargs["lat"]
        lon = kwargs["lon"]
        radius_m = kwargs["radius_m"]

        candidates: list[tuple[float, dict[str, Any]]] = []
        for gym in self._gyms:
            if not self._matches_filters(
                gym,
                min_conf=kwargs.get("min_conf"),
                tier=kwargs.get("tier"),
                specialty=kwargs.get("specialty"),
                lifter_friendly=kwargs.get("lifter_friendly"),
                is_24_7=kwargs.get("is_24_7"),
            ):
                continue
            distance = haversine_meters(lat, lon, gym["lat"], gym["lon"])
            if distance <= radius_m:
                candidates.append((distance, gym))

        candidates.sort(key=lambda item: item[0])
        return [gym for _, gym in candidates]


def _build_store_fixture(root: Path) -> DatasetGymStore:
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
                        "lat": QUERY_CENTER_LAT,
                        "lon": QUERY_CENTER_LON,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    results = []
    for idx in range(DATASET_SIZE):
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
                    "specialty": {
                        "value": "powerlifting" if idx % 9 == 0 else "general_fitness"
                    },
                },
            }
        )

    dataset_path.write_text(
        json.dumps({"schema_version": "1.2", "results": results}),
        encoding="utf-8",
    )

    registry = DatasetRegistry(registry_path).load()
    return DatasetGymStore(registry, cache_recheck_ns=60_000_000_000)


def _load_naive_fixture(root: Path) -> tuple[dict[str, Any], ...]:
    dataset_path = root / "gyms.json"
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    return tuple(payload["results"])


def _make_gym(idx: int) -> Gym:
    tags = {
        "name": f"Iron Club {idx}",
        "opening_hours": "24/7" if idx % 3 == 0 else "06:00-22:00",
        "website": f"https://gym{idx}.example.com",
        "sport": "fitness;weightlifting" if idx % 2 == 0 else "fitness",
        "leisure": "fitness_centre",
    }
    return Gym(
        name=tags["name"],
        norm_name=f"iron_club_{idx}",
        lat=36.0 + (idx % 100) * 0.0001,
        lon=-86.0 - (idx % 100) * 0.0001,
        osm_refs=[{"type": "node", "id": idx}],
        tags=tags,
    )


def _latency_summary(samples: list[float]) -> tuple[float, float, float]:
    ordered = sorted(samples)
    p95_index = max(int(len(ordered) * 0.95) - 1, 0)
    return statistics.mean(samples), statistics.median(samples), ordered[p95_index]


def _run_query_workload(
    store: Any,
    *,
    radius_m: float,
) -> tuple[list[int], list[float], float]:
    def _task(_: int) -> tuple[int, float]:
        started = time.perf_counter()
        results = list_gyms(
            store=store,
            region="profile",
            min_conf=0.7,
            specialty="powerlifting",
            lat=QUERY_CENTER_LAT,
            lon=QUERY_CENTER_LON,
            radius_m=radius_m,
            limit=100,
            offset=0,
        )
        duration = time.perf_counter() - started
        return len(results), duration

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=QUERY_WORKERS) as executor:
        outputs = list(executor.map(_task, range(QUERY_TASKS)))
    total = time.perf_counter() - started

    counts = [count for count, _ in outputs]
    samples = [sample for _, sample in outputs]
    return counts, samples, total


def _print_query_summary(
    label: str,
    counts: list[int],
    samples: list[float],
    total: float,
) -> None:
    mean_s, median_s, p95_s = _latency_summary(samples)
    print(f"  {label} mean size:    {statistics.mean(counts):.1f} results")
    print(f"  {label} throughput:   {QUERY_TASKS / total:.2f} ops/sec")
    print(f"  {label} mean:         {mean_s * 1000:.2f} ms")
    print(f"  {label} median:       {median_s * 1000:.2f} ms")
    print(f"  {label} p95:          {p95_s * 1000:.2f} ms")


def benchmark_query_concurrency(indexed_store: DatasetGymStore) -> None:
    naive_store = NaiveDatasetGymStore(
        _load_naive_fixture(Path(".tmp") / "profile-service")
    )

    for label, radius_m in (
        ("Broad Radius", BROAD_QUERY_RADIUS_M),
        ("Focused Radius", FOCUSED_QUERY_RADIUS_M),
    ):
        indexed_counts, indexed_samples, indexed_total = _run_query_workload(
            indexed_store,
            radius_m=radius_m,
        )
        naive_counts, naive_samples, naive_total = _run_query_workload(
            naive_store,
            radius_m=radius_m,
        )

        print("Concurrent Query Throughput")
        print(f"  scenario:             {label}")
        print(f"  radius_m:             {radius_m}")
        print(f"  tasks:                {QUERY_TASKS}")
        print(f"  workers:              {QUERY_WORKERS}")
        _print_query_summary("indexed", indexed_counts, indexed_samples, indexed_total)
        _print_query_summary("naive", naive_counts, naive_samples, naive_total)


def benchmark_inference_concurrency() -> None:
    def _task(idx: int) -> float:
        gym = _make_gym(idx)
        started = time.perf_counter()
        apply_inference(gym)
        return time.perf_counter() - started

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=INFERENCE_WORKERS) as executor:
        samples = list(executor.map(_task, range(INFERENCE_TASKS)))
    total = time.perf_counter() - started

    mean_s, median_s, p95_s = _latency_summary(samples)

    print("Concurrent Inference Throughput")
    print(f"  tasks:      {INFERENCE_TASKS}")
    print(f"  workers:    {INFERENCE_WORKERS}")
    print(f"  throughput: {INFERENCE_TASKS / total:.2f} ops/sec")
    print(f"  mean:       {mean_s * 1000:.3f} ms")
    print(f"  median:     {median_s * 1000:.3f} ms")
    print(f"  p95:        {p95_s * 1000:.3f} ms")


def main() -> None:
    print("GymDB Concurrent Profile")
    root = Path(".tmp") / "profile-service"
    store = _build_store_fixture(root)
    benchmark_query_concurrency(store)
    benchmark_inference_concurrency()


if __name__ == "__main__":
    os.environ.setdefault(
        "POSTGRES_DSN",
        "postgresql+psycopg://gymdb:gymdb_password@localhost:5432/gymdb",
    )
    main()
