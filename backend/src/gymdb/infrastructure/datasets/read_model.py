from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, cast

from gymdb.domain.constants import (
    INFERRED,
    IS_24_7,
    LIFTER_FRIENDLY,
    SPECIALTY,
    TIER,
)

_SQLITE_TIMEOUT_S = 30.0


def index_path_for_dataset(dataset_path: Path, dataset_mtime_ns: int) -> Path:
    return dataset_path.with_name(f"{dataset_path.stem}.{dataset_mtime_ns}.sqlite3")


def _parse_dataset_payload(
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


def _extract_inferred_value(gym: dict[str, Any], key: str) -> Any:
    inferred = gym.get(INFERRED)
    if not isinstance(inferred, dict):
        inferred = gym.get("inference")
    if not isinstance(inferred, dict):
        return None

    item = inferred.get(key)
    if isinstance(item, dict):
        return item.get("value")
    if hasattr(item, "value"):
        return cast(Any, item).value
    return None


def _as_optional_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _as_optional_bool(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    return None


def _cleanup_old_indexes(dataset_path: Path, keep_path: Path) -> None:
    pattern = f"{dataset_path.stem}.*.sqlite3"
    for candidate in dataset_path.parent.glob(pattern):
        if candidate == keep_path:
            continue
        try:
            candidate.unlink()
        except OSError:
            continue


def materialize_dataset_read_model(
    *,
    region: str,
    dataset_path: Path,
) -> Path:
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found for region `{region}`: {dataset_path}"
        )

    dataset_mtime_ns = dataset_path.stat().st_mtime_ns
    index_path = index_path_for_dataset(dataset_path, dataset_mtime_ns)
    if index_path.exists():
        return index_path

    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    gyms = _parse_dataset_payload(payload, region=region, path=dataset_path)

    temp_path = index_path.with_suffix(f"{index_path.suffix}.tmp")
    if temp_path.exists():
        temp_path.unlink()

    connection = sqlite3.connect(temp_path, timeout=_SQLITE_TIMEOUT_S)
    try:
        connection.execute("PRAGMA journal_mode = OFF")
        connection.execute("PRAGMA synchronous = OFF")
        connection.execute("PRAGMA temp_store = MEMORY")
        connection.execute(
            """
            CREATE TABLE gyms (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                tier TEXT,
                specialty TEXT,
                lifter_friendly INTEGER,
                is_24_7 INTEGER,
                lat REAL,
                lon REAL
            )
            """
        )
        connection.execute(
            "CREATE INDEX idx_gyms_confidence "
            "ON gyms(confidence_score DESC, id)"
        )
        connection.execute(
            "CREATE INDEX idx_gyms_tier_conf "
            "ON gyms(tier, confidence_score DESC, id)"
        )
        connection.execute(
            "CREATE INDEX idx_gyms_specialty_conf "
            "ON gyms(specialty, confidence_score DESC, id)"
        )
        connection.execute(
            "CREATE INDEX idx_gyms_lifter_conf "
            "ON gyms(lifter_friendly, confidence_score DESC, id)"
        )
        connection.execute(
            "CREATE INDEX idx_gyms_247_conf "
            "ON gyms(is_24_7, confidence_score DESC, id)"
        )
        connection.execute(
            "CREATE INDEX idx_gyms_geo_filter "
            "ON gyms(lat, lon, specialty, tier, confidence_score DESC, id)"
        )

        rows: list[tuple[Any, ...]] = []
        for gym in gyms:
            gym_id = gym.get("id")
            if not isinstance(gym_id, str) or not gym_id:
                continue
            rows.append(
                (
                    gym_id,
                    json.dumps(gym, separators=(",", ":"), ensure_ascii=True),
                    float(gym.get("confidence_score", 0.0)),
                    _extract_inferred_value(gym, TIER),
                    _extract_inferred_value(gym, SPECIALTY),
                    _as_optional_bool(_extract_inferred_value(gym, LIFTER_FRIENDLY)),
                    _as_optional_bool(_extract_inferred_value(gym, IS_24_7)),
                    _as_optional_float(gym.get("lat")),
                    _as_optional_float(gym.get("lon")),
                )
            )

        connection.executemany(
            """
            INSERT INTO gyms(
                id,
                payload,
                confidence_score,
                tier,
                specialty,
                lifter_friendly,
                is_24_7,
                lat,
                lon
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        connection.commit()
    finally:
        connection.close()

    temp_path.replace(index_path)
    _cleanup_old_indexes(dataset_path, index_path)
    return index_path
