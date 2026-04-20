from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from gymdb.infrastructure.live_search_cache import (
    load_cached_elements,
    prime_cache_from_dataset,
)


def _workspace_temp_root(name: str) -> Path:
    root = Path("tests") / ".tmp_live_search_cache" / f"{name}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_prime_cache_from_dataset_writes_default_cache():
    root = _workspace_temp_root("prime_writes")
    try:
        dataset_path = root / "gyms_default.json"
        dataset_path.write_text(
            json.dumps(
                {
                    "results": [
                        {
                            "id": "gym-1",
                            "name": "Default Gym",
                            "lat": 36.16,
                            "lon": -86.78,
                            "osm_refs": [{"type": "node", "id": 101}],
                            "tags": {"name": "Default Gym", "amenity": "gym"},
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        cache_root = root / "cache"
        cache_path = prime_cache_from_dataset(
            cache_root,
            dataset_path=dataset_path,
            lat=36.1663493,
            lon=-86.7790541,
            radius_m=16093,
            place_label="Nashville, TN",
        )

        assert cache_path is not None
        cached = load_cached_elements(
            cache_root,
            lat=36.1663493,
            lon=-86.7790541,
            radius_m=16093,
        )
        assert cached is not None
        assert cached.elements == [
            {
                "type": "node",
                "id": 101,
                "lat": 36.16,
                "lon": -86.78,
                "tags": {"name": "Default Gym", "amenity": "gym"},
            }
        ]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_prime_cache_from_dataset_preserves_existing_cache_by_default():
    root = _workspace_temp_root("prime_preserves")
    try:
        dataset_path = root / "gyms_default.json"
        dataset_path.write_text(
            json.dumps(
                {
                    "results": [
                        {
                            "id": "gym-1",
                            "name": "Updated Gym",
                            "lat": 36.16,
                            "lon": -86.78,
                            "osm_refs": [{"type": "node", "id": 101}],
                            "tags": {"name": "Updated Gym", "amenity": "gym"},
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        cache_root = root / "cache"
        prime_cache_from_dataset(
            cache_root,
            dataset_path=dataset_path,
            lat=36.1663493,
            lon=-86.7790541,
            radius_m=16093,
            place_label="Nashville, TN",
        )

        first_cache = load_cached_elements(
            cache_root,
            lat=36.1663493,
            lon=-86.7790541,
            radius_m=16093,
        )
        assert first_cache is not None

        dataset_path.write_text(
            json.dumps(
                {
                    "results": [
                        {
                            "id": "gym-1",
                            "name": "Another Gym",
                            "lat": 36.16,
                            "lon": -86.78,
                            "osm_refs": [{"type": "node", "id": 101}],
                            "tags": {"name": "Another Gym", "amenity": "gym"},
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        second_path = prime_cache_from_dataset(
            cache_root,
            dataset_path=dataset_path,
            lat=36.1663493,
            lon=-86.7790541,
            radius_m=16093,
            place_label="Nashville, TN",
        )
        second_cache = load_cached_elements(
            cache_root,
            lat=36.1663493,
            lon=-86.7790541,
            radius_m=16093,
        )

        assert second_path == first_cache.cache_path
        assert second_cache is not None
        assert second_cache.elements == first_cache.elements
    finally:
        shutil.rmtree(root, ignore_errors=True)
