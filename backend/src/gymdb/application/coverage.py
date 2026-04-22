from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Any

from gymdb.domain.models import Gym
from gymdb.domain.processing import haversine_meters, normalize_name
from gymdb.domain.provenance import (
    OSM_ENRICH_KEYS,
    OSM_MATCH_DISTANCE_METERS,
    ConfirmedBy,
    MatchStatus,
)
from gymdb.infrastructure.tomtom_client import TomTomPlace

MATCH_DISTANCE_METERS = 250.0


@dataclass(frozen=True)
class CoverageMatch:
    status: str
    osm_name: str | None
    tomtom_name: str | None
    distance_m: float | None
    osm_id: str | None
    tomtom_id: str | None
    city: str | None
    url: str | None


@dataclass(frozen=True)
class CoverageSummary:
    matched: int
    name_mismatch: int
    missing_from_osm: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


GymRecord = Gym | dict[str, Any]


def _gym_name(gym: GymRecord) -> str:
    if isinstance(gym, Gym):
        return gym.name
    return str(gym.get("name") or "")


def _gym_norm_name(gym: GymRecord) -> str:
    if isinstance(gym, Gym):
        return gym.norm_name
    return str(gym.get("norm_name") or normalize_name(_gym_name(gym)))


def _gym_id(gym: GymRecord) -> str | None:
    if isinstance(gym, Gym):
        return gym.id
    value = gym.get("id")
    return None if value is None else str(value)


def _gym_lat_lon(gym: GymRecord) -> tuple[float, float]:
    if isinstance(gym, Gym):
        return gym.lat, gym.lon
    return float(gym["lat"]), float(gym["lon"])


def _choose_better_match(
    current: CoverageMatch | None,
    candidate: CoverageMatch,
) -> CoverageMatch:
    if current is None:
        return candidate

    rank = {"matched": 2, "name_mismatch": 1}
    current_rank = rank.get(current.status, 0)
    candidate_rank = rank.get(candidate.status, 0)
    if candidate_rank > current_rank:
        return candidate
    if candidate_rank < current_rank:
        return current

    current_distance = (
        current.distance_m if current.distance_m is not None else float("inf")
    )
    candidate_distance = (
        candidate.distance_m if candidate.distance_m is not None else float("inf")
    )
    if candidate_distance < current_distance:
        return candidate
    return current


def best_osm_match(
    place: TomTomPlace,
    gyms: Iterable[GymRecord],
) -> tuple[GymRecord | None, float | None]:
    normalized_target = normalize_name(place.name)
    best_gym: GymRecord | None = None
    best_distance: float | None = None

    gym_list = list(gyms)

    for candidate in gym_list:
        distance = haversine_meters(place.lat, place.lon, *_gym_lat_lon(candidate))
        if (
            _gym_norm_name(candidate) == normalized_target
            and distance <= MATCH_DISTANCE_METERS
        ):
            if best_distance is None or distance < best_distance:
                best_gym = candidate
                best_distance = distance

    if best_gym is not None:
        return best_gym, best_distance

    for candidate in gym_list:
        distance = haversine_meters(place.lat, place.lon, *_gym_lat_lon(candidate))
        if distance <= MATCH_DISTANCE_METERS:
            gym_norm = _gym_norm_name(candidate)
            if gym_norm.startswith(normalized_target) or normalized_target.startswith(
                gym_norm
            ):
                if best_distance is None or distance < best_distance:
                    best_gym = candidate
                    best_distance = distance

    return best_gym, best_distance


def classify(
    place: TomTomPlace,
    gym: GymRecord | None,
    distance_m: float | None,
) -> CoverageMatch:
    if gym is None:
        return CoverageMatch(
            status="missing_from_osm",
            osm_name=None,
            tomtom_name=place.name,
            distance_m=None,
            osm_id=None,
            tomtom_id=place.id,
            city=place.city,
            url=place.url,
        )

    osm_name = _gym_name(gym)
    osm_id = _gym_id(gym)
    same_name = normalize_name(osm_name) == normalize_name(place.name)
    status = "matched" if same_name else "name_mismatch"

    return CoverageMatch(
        status=status,
        osm_name=osm_name,
        tomtom_name=place.name,
        distance_m=distance_m,
        osm_id=osm_id,
        tomtom_id=place.id,
        city=place.city,
        url=place.url,
    )


def summarize_matches(matches: list[CoverageMatch]) -> CoverageSummary:
    return CoverageSummary(
        matched=sum(1 for match in matches if match.status == "matched"),
        name_mismatch=sum(1 for match in matches if match.status == "name_mismatch"),
        missing_from_osm=sum(
            1 for match in matches if match.status == "missing_from_osm"
        ),
    )


def apply_tomtom_coverage(
    gyms: list[Gym],
    places: Iterable[TomTomPlace],
) -> tuple[list[CoverageMatch], CoverageSummary]:
    best_by_gym: dict[str, CoverageMatch] = {}
    matches: list[CoverageMatch] = []

    for gym in gyms:
        gym.source_provenance = {
            "primary": "osm",
            "confirmed_by": [],
            "match_status": "unconfirmed",
            "external_refs": {},
        }

    for place in places:
        matched_gym, distance_m = best_osm_match(place, gyms)
        match = classify(place, matched_gym, distance_m)
        matches.append(match)
        if match.osm_id is None:
            continue
        best_by_gym[match.osm_id] = _choose_better_match(
            best_by_gym.get(match.osm_id),
            match,
        )

    gyms_by_id: dict[str, Gym] = {gym.id: gym for gym in gyms if gym.id is not None}
    for gym_id, match in best_by_gym.items():
        matched_gym = gyms_by_id.get(gym_id)
        if matched_gym is None:
            continue
        confirmed_by = ["tomtom"] if match.status == "matched" else []
        matched_gym.source_provenance = {
            "primary": "osm",
            "confirmed_by": confirmed_by,
            "match_status": match.status,
            "external_refs": {
                "tomtom": {
                    "provider": "tomtom",
                    "external_id": match.tomtom_id,
                    "name": match.tomtom_name,
                    "distance_m": match.distance_m,
                    "city": match.city,
                    "url": match.url,
                    "status": match.status,
                }
            },
        }

    return matches, summarize_matches(matches)


def apply_osm_confirmation(
    gyms: list[Gym],
    osm_elements: list[dict[str, Any]],
) -> None:
    """
    Cross-validate TomTom-primary gyms against cached OSM elements.

    For each gym whose match_status is TOMTOM_ONLY, find the closest OSM element
    within OSM_MATCH_DISTANCE_METERS:
    - Exact normalised name match → OSM_CONFIRMED, confirmed_by=[ConfirmedBy.OSM]
    - Any element within distance (name mismatch) → OSM_NEARBY
    - No element within distance → unchanged (stays TOMTOM_ONLY)

    OSM tag keys in OSM_ENRICH_KEYS are merged onto the gym if not already present.
    This function mutates gyms in place and returns None.
    """
    if not osm_elements:
        return

    # Pre-normalise OSM element names and extract lat/lon once.
    prepared: list[tuple[str, float, float, dict[str, Any]]] = []
    for el in osm_elements:
        tags = el.get("tags")
        if not isinstance(tags, dict):
            continue
        raw_lat = el.get("lat")
        raw_lon = el.get("lon")
        if not isinstance(raw_lat, (int, float)) or not isinstance(raw_lon, (int, float)):
            continue
        name = str(tags.get("name") or "")
        prepared.append((normalize_name(name), float(raw_lat), float(raw_lon), tags))

    for gym in gyms:
        provenance = gym.source_provenance or {}
        if provenance.get("match_status") != MatchStatus.TOMTOM_ONLY.value:
            continue

        gym_norm = gym.norm_name
        best_status: str | None = None
        best_distance: float = float("inf")
        best_tags: dict[str, Any] | None = None

        for osm_norm, osm_lat, osm_lon, osm_tags in prepared:
            distance = haversine_meters(gym.lat, gym.lon, osm_lat, osm_lon)
            if distance > OSM_MATCH_DISTANCE_METERS:
                continue

            if osm_norm == gym_norm:
                # Exact name — OSM_CONFIRMED; always prefer over OSM_NEARBY.
                if (
                    best_status != MatchStatus.OSM_CONFIRMED.value
                    or distance < best_distance
                ):
                    best_status = MatchStatus.OSM_CONFIRMED.value
                    best_distance = distance
                    best_tags = osm_tags
            elif best_status != MatchStatus.OSM_CONFIRMED.value:
                # Name mismatch but spatially close — OSM_NEARBY.
                if distance < best_distance:
                    best_status = MatchStatus.OSM_NEARBY.value
                    best_distance = distance
                    best_tags = osm_tags

        if best_status is None:
            continue

        confirmed_by = (
            [ConfirmedBy.OSM.value]
            if best_status == MatchStatus.OSM_CONFIRMED.value
            else []
        )
        gym.source_provenance = {
            **provenance,
            "confirmed_by": confirmed_by,
            "match_status": best_status,
        }

        # Merge OSM enrichment tags; never overwrite existing values.
        if best_tags:
            for key in OSM_ENRICH_KEYS:
                if key in best_tags and key not in gym.tags:
                    gym.tags[key] = best_tags[key]
