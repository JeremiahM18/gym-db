from __future__ import annotations

import json
import os
import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, cast

from gymdb.domain.constants import (
    INFERRED,
    IS_24_7,
    LIFTER_FRIENDLY,
    SPECIALTY,
    TIER,
)

_LOCK_TIMEOUT_S = 30.0
_LOCK_POLL_S = 0.05
_SQLITE_TIMEOUT_S = 30.0


def index_path_for_dataset(dataset_path: Path, dataset_mtime_ns: int) -> Path:
    return dataset_path.with_name(f"{dataset_path.stem}.{dataset_mtime_ns}.sqlite3")


def manifest_path_for_dataset(dataset_path: Path) -> Path:
    return dataset_path.with_name(f"{dataset_path.stem}.manifest.json")


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


@contextmanager
def _dataset_lock(dataset_path: Path) -> Iterator[None]:
    lock_path = dataset_path.with_suffix(f"{dataset_path.suffix}.lock")
    started = time.monotonic()

    while True:
        try:
            fd = os.open(
                str(lock_path),
                os.O_CREAT | os.O_EXCL | os.O_RDWR,
            )
            break
        except FileExistsError as exc:
            if time.monotonic() - started >= _LOCK_TIMEOUT_S:
                raise TimeoutError(
                    f"Timed out waiting for dataset lock: {lock_path}"
                ) from exc
            time.sleep(_LOCK_POLL_S)

    try:
        os.write(fd, str(os.getpid()).encode("ascii", errors="ignore"))
        yield
    finally:
        os.close(fd)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def _write_manifest(
    *,
    dataset_path: Path,
    dataset_mtime_ns: int,
    index_path: Path,
) -> None:
    manifest = {
        "dataset_file": dataset_path.name,
        "dataset_mtime_ns": dataset_mtime_ns,
        "read_model_file": index_path.name,
        "generated_at_ns": time.time_ns(),
    }
    manifest_path = manifest_path_for_dataset(dataset_path)
    with NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=manifest_path.parent,
        prefix=f"{manifest_path.stem}.",
        suffix=".tmp",
        delete=False,
    ) as temp_file:
        json.dump(manifest, temp_file, indent=2)
        temp_path = Path(temp_file.name)

    temp_path.replace(manifest_path)


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
        _write_manifest(
            dataset_path=dataset_path,
            dataset_mtime_ns=dataset_mtime_ns,
            index_path=index_path,
        )
        return index_path

    with _dataset_lock(dataset_path):
        dataset_mtime_ns = dataset_path.stat().st_mtime_ns
        index_path = index_path_for_dataset(dataset_path, dataset_mtime_ns)
        if index_path.exists():
            _write_manifest(
                dataset_path=dataset_path,
                dataset_mtime_ns=dataset_mtime_ns,
                index_path=index_path,
            )
            return index_path

        payload = json.loads(dataset_path.read_text(encoding="utf-8"))
        gyms = _parse_dataset_payload(payload, region=region, path=dataset_path)

        with NamedTemporaryFile(
            suffix=".sqlite3.tmp",
            prefix=f"{index_path.stem}.",
            dir=index_path.parent,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)

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
                        _as_optional_bool(
                            _extract_inferred_value(gym, LIFTER_FRIENDLY)
                        ),
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
        _write_manifest(
            dataset_path=dataset_path,
            dataset_mtime_ns=dataset_mtime_ns,
            index_path=index_path,
        )
        return index_path
