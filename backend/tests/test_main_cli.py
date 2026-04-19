import pytest

from gymdb.infrastructure.tomtom_client import TomTomPlace
from main import resolve_place_query, slugify_region_key


def test_slugify_region_key_normalizes_place_names():
    assert slugify_region_key("Franklin, TN") == "franklin_tn"
    assert slugify_region_key("  New York / Brooklyn  ") == "new_york_brooklyn"


def test_resolve_place_query_requires_tomtom_key(monkeypatch):
    monkeypatch.setattr("main.settings.tomtom_api_key", None)

    with pytest.raises(SystemExit, match="TOMTOM_API_KEY"):
        resolve_place_query("Franklin, TN")


def test_resolve_place_query_returns_first_match(monkeypatch):
    monkeypatch.setattr("main.settings.tomtom_api_key", "test-key")
    monkeypatch.setattr(
        "main.TomTomClient.geocode",
        lambda self, query, limit=5: [
            TomTomPlace(
                id="place-1",
                name="Franklin, TN",
                lat=35.9236,
                lon=-86.8678,
                address="Franklin, TN",
                city="Franklin",
                country_code="US",
                url=None,
                raw={},
            )
        ],
    )

    result = resolve_place_query("Franklin, TN")

    assert result.name == "Franklin, TN"
    assert result.lat == 35.9236
