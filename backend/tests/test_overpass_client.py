from __future__ import annotations

import requests

from gymdb.infrastructure.overpass_client import (
    OverpassUnavailableError,
    fetch_gyms,
)


class FakeResponse:
    def __init__(
        self,
        *,
        payload: dict | None = None,
        status_code: int = 200,
        raise_http: bool = False,
    ):
        self._payload = payload or {"elements": []}
        self.status_code = status_code
        self._raise_http = raise_http

    def raise_for_status(self) -> None:
        if self._raise_http:
            raise requests.HTTPError("boom", response=self)

    def json(self) -> dict:
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls: list[str] = []

    def post(self, url: str, *, data: str, timeout: int):
        self.calls.append(url)
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_fetch_gyms_retries_timeout_then_succeeds(monkeypatch):
    monkeypatch.setattr(
        "gymdb.infrastructure.overpass_client.settings.overpass_url",
        "https://primary.example/api/interpreter",
    )
    monkeypatch.setattr(
        "gymdb.infrastructure.overpass_client.settings.overpass_fallback_url",
        None,
    )
    monkeypatch.setattr(
        "gymdb.infrastructure.overpass_client.settings.overpass_max_attempts",
        2,
    )
    monkeypatch.setattr(
        "gymdb.infrastructure.overpass_client.settings.overpass_timeout_seconds",
        30,
    )
    sleep_calls: list[float] = []
    session = FakeSession(
        [
            requests.Timeout("timed out"),
            FakeResponse(payload={"elements": [{"id": 1}]}),
        ]
    )

    elements = fetch_gyms(
        1000,
        36.16,
        -86.78,
        session=session,
        sleep_fn=sleep_calls.append,
    )

    assert elements == [{"id": 1}]
    assert session.calls == [
        "https://primary.example/api/interpreter",
        "https://primary.example/api/interpreter",
    ]
    assert sleep_calls == [2.0]


def test_fetch_gyms_uses_fallback_endpoint_after_retryable_http_error(monkeypatch):
    monkeypatch.setattr(
        "gymdb.infrastructure.overpass_client.settings.overpass_url",
        "https://primary.example/api/interpreter",
    )
    monkeypatch.setattr(
        "gymdb.infrastructure.overpass_client.settings.overpass_fallback_url",
        "https://fallback.example/api/interpreter",
    )
    monkeypatch.setattr(
        "gymdb.infrastructure.overpass_client.settings.overpass_max_attempts",
        1,
    )
    session = FakeSession(
        [
            FakeResponse(status_code=504, raise_http=True),
            FakeResponse(payload={"elements": [{"id": 2}]}),
        ]
    )

    elements = fetch_gyms(
        1000,
        36.16,
        -86.78,
        session=session,
        sleep_fn=lambda _: None,
    )

    assert elements == [{"id": 2}]
    assert session.calls == [
        "https://primary.example/api/interpreter",
        "https://fallback.example/api/interpreter",
    ]


def test_fetch_gyms_raises_helpful_error_after_exhausting_retries(monkeypatch):
    monkeypatch.setattr(
        "gymdb.infrastructure.overpass_client.settings.overpass_url",
        "https://primary.example/api/interpreter",
    )
    monkeypatch.setattr(
        "gymdb.infrastructure.overpass_client.settings.overpass_fallback_url",
        None,
    )
    monkeypatch.setattr(
        "gymdb.infrastructure.overpass_client.settings.overpass_max_attempts",
        2,
    )
    session = FakeSession(
        [
            requests.Timeout("gateway timeout"),
            requests.Timeout("still bad"),
        ]
    )

    try:
        fetch_gyms(
            1000,
            36.16,
            -86.78,
            session=session,
            sleep_fn=lambda _: None,
        )
    except OverpassUnavailableError as exc:
        assert "alternate OVERPASS_FALLBACK_URL" in str(exc)
        assert "still bad" in str(exc)
    else:
        raise AssertionError("Expected OverpassUnavailableError")


def test_fetch_gyms_raises_immediately_for_non_retryable_http_error(monkeypatch):
    monkeypatch.setattr(
        "gymdb.infrastructure.overpass_client.settings.overpass_url",
        "https://primary.example/api/interpreter",
    )
    monkeypatch.setattr(
        "gymdb.infrastructure.overpass_client.settings.overpass_fallback_url",
        None,
    )
    monkeypatch.setattr(
        "gymdb.infrastructure.overpass_client.settings.overpass_max_attempts",
        3,
    )
    session = FakeSession([FakeResponse(status_code=400, raise_http=True)])

    try:
        fetch_gyms(
            1000,
            36.16,
            -86.78,
            session=session,
            sleep_fn=lambda _: None,
        )
    except OverpassUnavailableError as exc:
        assert "non-retryable HTTP error (400)" in str(exc)
    else:
        raise AssertionError("Expected OverpassUnavailableError")


def test_fetch_gyms_uses_fallback_after_non_retryable_http_error(monkeypatch):
    monkeypatch.setattr(
        "gymdb.infrastructure.overpass_client.settings.overpass_url",
        "https://primary.example/api/interpreter",
    )
    monkeypatch.setattr(
        "gymdb.infrastructure.overpass_client.settings.overpass_fallback_url",
        "https://fallback.example/api/interpreter",
    )
    monkeypatch.setattr(
        "gymdb.infrastructure.overpass_client.settings.overpass_max_attempts",
        1,
    )
    session = FakeSession(
        [
            FakeResponse(status_code=403, raise_http=True),
            FakeResponse(payload={"elements": [{"id": 3}]}),
        ]
    )

    elements = fetch_gyms(
        1000,
        36.16,
        -86.78,
        session=session,
        sleep_fn=lambda _: None,
    )

    assert elements == [{"id": 3}]
    assert session.calls == [
        "https://primary.example/api/interpreter",
        "https://fallback.example/api/interpreter",
    ]
