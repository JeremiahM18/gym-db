from __future__ import annotations

from typing import Any

from gymdb.gyms.protocol import GymStoreProtocol

_REVIEWABLE_STATUSES = {"matched", "name_mismatch", "unconfirmed"}


def _match_status(gym: dict[str, Any]) -> str:
    provenance = gym.get("source_provenance")
    if not isinstance(provenance, dict):
        return "unconfirmed"
    return str(provenance.get("match_status") or "unconfirmed")


def _has_contradictions(gym: dict[str, Any]) -> bool:
    meta = gym.get("inference_meta")
    if not isinstance(meta, dict):
        return False
    contradictions = meta.get("contradictions")
    return isinstance(contradictions, dict) and any(contradictions.values())


def list_review_gyms(
    *,
    store: GymStoreProtocol,
    region: str,
    status: str | None = None,
    max_conf: float | None = None,
    contradictions_only: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    gyms = store.filter(
        region=region,
        min_conf=None,
        limit=max(limit + offset, 500),
        offset=0,
    )

    if status is not None:
        if status not in _REVIEWABLE_STATUSES:
            raise ValueError(f"Unsupported review status: {status}")
        gyms = [gym for gym in gyms if _match_status(gym) == status]

    if max_conf is not None:
        gyms = [
            gym
            for gym in gyms
            if float(gym.get("confidence_score") or 0.0) <= max_conf
        ]

    if contradictions_only:
        gyms = [gym for gym in gyms if _has_contradictions(gym)]

    gyms.sort(
        key=lambda gym: (
            float(gym.get("confidence_score") or 0.0),
            gym.get("name") or "",
        )
    )
    return gyms[offset : offset + limit]


def summarize_review_gyms(
    *,
    store: GymStoreProtocol,
    region: str,
) -> dict[str, int]:
    gyms = store.filter(region=region, min_conf=None, limit=10_000, offset=0)
    summary = {
        "matched": 0,
        "name_mismatch": 0,
        "unconfirmed": 0,
        "contradictions": 0,
        "low_confidence": 0,
    }

    for gym in gyms:
        status = _match_status(gym)
        summary[status if status in summary else "unconfirmed"] += 1
        if _has_contradictions(gym):
            summary["contradictions"] += 1
        if float(gym.get("confidence_score") or 0.0) < 0.5:
            summary["low_confidence"] += 1

    return summary
