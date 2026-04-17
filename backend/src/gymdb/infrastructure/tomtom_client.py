from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import requests


@dataclass(frozen=True)
class TomTomPlace:
    id: str
    name: str
    lat: float
    lon: float
    address: str | None
    city: str | None
    country_code: str | None
    url: str | None
    raw: dict[str, Any]


class TomTomClient:
    def __init__(self, *, api_key: str, base_url: str = "https://api.tomtom.com"):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    def _parse_places(self, payload: dict[str, Any]) -> list[TomTomPlace]:
        results: list[TomTomPlace] = []
        for item in payload.get("results", []):
            position = item.get("position", {})
            poi = item.get("poi", {})
            address = item.get("address", {})
            place_id = str(item.get("id") or poi.get("id") or poi.get("name") or "")
            name = str(
                poi.get("name") or item.get("address", {}).get("freeformAddress") or ""
            ).strip()
            lat_value = position.get("lat")
            lon_value = position.get("lon")
            if not place_id or not name or lat_value is None or lon_value is None:
                continue
            results.append(
                TomTomPlace(
                    id=place_id,
                    name=name,
                    lat=float(lat_value),
                    lon=float(lon_value),
                    address=address.get("freeformAddress"),
                    city=address.get("municipality"),
                    country_code=address.get("countryCode"),
                    url=poi.get("url"),
                    raw=item,
                )
            )
        return results

    def search_gyms(
        self,
        *,
        lat: float,
        lon: float,
        radius_m: int,
        limit: int = 100,
        country_set: str = "US",
    ) -> list[TomTomPlace]:
        params: dict[str, str | int | float] = {
            "key": self._api_key,
            "lat": lat,
            "lon": lon,
            "radius": radius_m,
            "limit": limit,
            "countrySet": country_set,
        }
        response = requests.get(
            f"{self._base_url}/search/2/categorySearch/gym.json",
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return self._parse_places(response.json())

    def geocode(
        self,
        *,
        query: str,
        limit: int = 5,
        country_set: str = "US",
    ) -> list[TomTomPlace]:
        params: dict[str, str | int] = {
            "key": self._api_key,
            "limit": limit,
            "countrySet": country_set,
        }
        encoded_query = quote(query, safe="")
        response = requests.get(
            f"{self._base_url}/search/2/geocode/{encoded_query}.json",
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return self._parse_places(response.json())
