from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _coerce_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value.astimezone(UTC)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).astimezone(UTC)
        except ValueError:
            return None
    return None


@dataclass(frozen=True)
class LiveSearchSession:
    search_id: str
    owner_sub: str
    status: str
    enrichment_status: str
    revision: int
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    response: dict[str, Any]

    @property
    def is_expired(self) -> bool:
        return self.expires_at <= _utc_now()

    def to_api_response(self, *, poll_after_ms: int | None) -> dict[str, Any]:
        return {
            **self.response,
            "search_id": self.search_id,
            "status": self.status,
            "enrichment_status": self.enrichment_status,
            "revision": self.revision,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "poll_after_ms": poll_after_ms if self.status == "enriching" else None,
        }


def build_live_search_session_id() -> str:
    return secrets.token_urlsafe(12)


def live_search_session_path(session_root: Path, search_id: str) -> Path:
    return session_root / f"{search_id}.json"


def create_live_search_session(
    session_root: Path,
    *,
    owner_sub: str,
    response: dict[str, Any],
    status: str,
    enrichment_status: str,
    ttl_seconds: int,
) -> LiveSearchSession:
    now = _utc_now()
    session = LiveSearchSession(
        search_id=build_live_search_session_id(),
        owner_sub=owner_sub,
        status=status,
        enrichment_status=enrichment_status,
        revision=0,
        created_at=now,
        updated_at=now,
        expires_at=now + timedelta(seconds=ttl_seconds),
        response=response,
    )
    write_live_search_session(session_root, session)
    return session


def load_live_search_session(
    session_root: Path,
    search_id: str,
) -> LiveSearchSession | None:
    session_path = live_search_session_path(session_root, search_id)
    if not session_path.exists():
        return None

    try:
        payload = json.loads(session_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    session = _parse_live_search_session(payload)
    if session is None:
        return None
    if session.is_expired:
        try:
            session_path.unlink(missing_ok=True)
        except OSError:
            pass
        return None
    return session


def write_live_search_session(
    session_root: Path,
    session: LiveSearchSession,
) -> Path:
    session_root.mkdir(parents=True, exist_ok=True)
    session_path = live_search_session_path(session_root, session.search_id)
    payload = {
        "search_id": session.search_id,
        "owner_sub": session.owner_sub,
        "status": session.status,
        "enrichment_status": session.enrichment_status,
        "revision": session.revision,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "expires_at": session.expires_at.isoformat(),
        "response": session.response,
    }
    with NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=session_root,
        prefix=f"{session.search_id}.",
        suffix=".tmp",
        delete=False,
    ) as temp_file:
        json.dump(payload, temp_file, indent=2, default=str)
        temp_path = Path(temp_file.name)

    temp_path.replace(session_path)
    return session_path


def replace_live_search_session(
    session_root: Path,
    session: LiveSearchSession,
    *,
    response: dict[str, Any] | None = None,
    status: str | None = None,
    enrichment_status: str | None = None,
    revision_delta: int = 1,
) -> LiveSearchSession:
    updated = LiveSearchSession(
        search_id=session.search_id,
        owner_sub=session.owner_sub,
        status=status or session.status,
        enrichment_status=enrichment_status or session.enrichment_status,
        revision=session.revision + revision_delta,
        created_at=session.created_at,
        updated_at=_utc_now(),
        expires_at=session.expires_at,
        response=response or session.response,
    )
    write_live_search_session(session_root, updated)
    return updated


def _parse_live_search_session(payload: Any) -> LiveSearchSession | None:
    if not isinstance(payload, dict):
        return None

    search_id = payload.get("search_id")
    owner_sub = payload.get("owner_sub")
    status = payload.get("status")
    enrichment_status = payload.get("enrichment_status")
    revision = payload.get("revision")
    created_at = _coerce_datetime(payload.get("created_at"))
    updated_at = _coerce_datetime(payload.get("updated_at"))
    expires_at = _coerce_datetime(payload.get("expires_at"))
    response = payload.get("response")

    if not isinstance(search_id, str) or not search_id:
        return None
    if not isinstance(owner_sub, str) or not owner_sub:
        return None
    if not isinstance(status, str) or not status:
        return None
    if not isinstance(enrichment_status, str) or not enrichment_status:
        return None
    if not isinstance(revision, int) or revision < 0:
        return None
    if created_at is None or updated_at is None or expires_at is None:
        return None
    if not isinstance(response, dict):
        return None

    return LiveSearchSession(
        search_id=search_id,
        owner_sub=owner_sub,
        status=status,
        enrichment_status=enrichment_status,
        revision=revision,
        created_at=created_at,
        updated_at=updated_at,
        expires_at=expires_at,
        response=response,
    )
