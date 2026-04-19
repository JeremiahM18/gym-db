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

    def _get(
        self,
        path: str,
        *,
        params: dict[str, str | int | float],
        timeout: int = 30,
    ) -> dict[str, Any]:
        response = requests.get(
            f"{self._base_url}{path}",
            params={"key": self._api_key, **params},
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()

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
        payload = self._get(
            "/search/2/categorySearch/gym.json",
            params={
                "lat": lat,
                "lon": lon,
                "radius": radius_m,
                "limit": limit,
                "countrySet": country_set,
            },
        )
        return self._parse_places(payload)

    def search(
        self,
        *,
        query: str,
        limit: int = 25,
        country_set: str = "US",
        lat: float | None = None,
        lon: float | None = None,
        radius_m: int | None = None,
        geobias_lat: float | None = None,
        geobias_lon: float | None = None,
    ) -> list[TomTomPlace]:
        params: dict[str, str | int | float] = {
            "limit": limit,
            "countrySet": country_set,
            "idxSet": "POI",
        }
        if lat is not None and lon is not None:
            params["lat"] = lat
            params["lon"] = lon
        if radius_m is not None:
            params["radius"] = radius_m
        if geobias_lat is not None and geobias_lon is not None:
            params["geobias"] = f"point:{geobias_lat},{geobias_lon}"

        encoded_query = quote(query, safe="")
        payload = self._get(
            f"/search/2/search/{encoded_query}.json",
            params=params,
        )
        return self._parse_places(payload)

    def category_search(
        self,
        *,
        category: str,
        lat: float,
        lon: float,
        radius_m: int,
        limit: int = 25,
        country_set: str = "US",
    ) -> list[TomTomPlace]:
        encoded_category = quote(category, safe="")
        payload = self._get(
            f"/search/2/categorySearch/{encoded_category}.json",
            params={
                "lat": lat,
                "lon": lon,
                "radius": radius_m,
                "limit": limit,
                "countrySet": country_set,
            },
        )
        return self._parse_places(payload)

    def geocode(
        self,
        *,
        query: str,
        limit: int = 5,
        country_set: str = "US",
    ) -> list[TomTomPlace]:
        encoded_query = quote(query, safe="")
        payload = self._get(
            f"/search/2/geocode/{encoded_query}.json",
            params={
                "limit": limit,
                "countrySet": country_set,
            },
        )
        return self._parse_places(payload)
