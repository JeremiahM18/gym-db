from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import requests

from gymdb.infrastructure.settings import settings


class OverpassUnavailableError(RuntimeError):
    """Raised when the upstream Overpass service cannot satisfy the ingest query."""


_RETRYABLE_STATUS_CODES = {429, 502, 503, 504}


def build_query(radius_meters: float, lat: float, lon: float) -> str:
    # Pull both common gym tags in OSM:
    # leisure=fitness_centre
    # amenity=gym
    return f"""
[out:json][timeout:25];
(
    node["leisure"="fitness_centre"](around:{radius_meters},{lat},{lon});
    way["leisure"="fitness_centre"](around:{radius_meters},{lat},{lon});
    relation["leisure"="fitness_centre"](around:{radius_meters},{lat},{lon});

    node["amenity"="gym"](around:{radius_meters},{lat},{lon});
    way["amenity"="gym"](around:{radius_meters},{lat},{lon});
    relation["amenity"="gym"](around:{radius_meters},{lat},{lon});
);
out center tags;
"""


def _candidate_urls() -> list[str]:
    urls: list[str] = [settings.overpass_url]
    fallback = settings.overpass_fallback_url
    if fallback and fallback not in urls:
        urls.append(fallback)
    return urls


def _is_retryable_http_error(error: requests.HTTPError) -> bool:
    response = error.response
    return response is not None and response.status_code in _RETRYABLE_STATUS_CODES


def _http_status_code(error: requests.HTTPError) -> int | str:
    response = error.response
    return response.status_code if response is not None else "unknown"


def _retry_sleep(
    sleep_fn: Callable[[float], None],
    *,
    attempt: int,
    backoff_seconds: float,
) -> None:
    sleep_fn(backoff_seconds * attempt)


def fetch_gyms(
    radius_meters: float,
    lat: float,
    lon: float,
    *,
    session: requests.Session | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    timeout_seconds: int | None = None,
    max_attempts: int | None = None,
    backoff_seconds: float | None = None,
) -> list[dict[str, Any]]:
    query = build_query(radius_meters, lat, lon)
    http = session or requests.Session()
    last_error: Exception | None = None
    urls = _candidate_urls()
    total_attempts = max(max_attempts or settings.overpass_max_attempts, 1)
    request_timeout_seconds = timeout_seconds or settings.overpass_timeout_seconds
    retry_backoff_seconds = (
        backoff_seconds
        if backoff_seconds is not None
        else settings.overpass_backoff_seconds
    )

    for url_index, url in enumerate(urls):
        for attempt in range(1, total_attempts + 1):
            try:
                response = http.post(
                    url,
                    data=query,
                    timeout=request_timeout_seconds,
                )
                response.raise_for_status()
                payload = response.json()
                return payload.get("elements", [])
            except requests.Timeout as exc:
                last_error = exc
            except requests.ConnectionError as exc:
                last_error = exc
            except requests.HTTPError as exc:
                last_error = exc
                if not _is_retryable_http_error(exc):
                    status_code = _http_status_code(exc)
                    is_last_url = url_index == len(urls) - 1
                    if not is_last_url:
                        break
                    raise OverpassUnavailableError(
                        "Overpass returned a non-retryable HTTP error "
                        f"({status_code}) while fetching gyms."
                    ) from exc

            is_last_attempt = attempt == total_attempts
            is_last_url = url_index == len(urls) - 1
            if is_last_attempt and is_last_url:
                break
            _retry_sleep(
                sleep_fn,
                attempt=attempt,
                backoff_seconds=retry_backoff_seconds,
            )

    detail = str(last_error) if last_error else "unknown upstream failure"
    raise OverpassUnavailableError(
        "Gym ingest could not fetch data from Overpass after retrying configured "
        f"endpoint(s). Try a smaller radius, wait a moment, or configure an "
        f"alternate OVERPASS_FALLBACK_URL. Last error: {detail}"
    ) from last_error
