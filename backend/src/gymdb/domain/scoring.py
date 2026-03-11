from __future__ import annotations

from gymdb.domain.models import Gym

GENERIC_NAMES = {
    "gym",
    "fitness",
    "fitness center",
    "fitness centre",
    "health club",
    "ymca",
}

_ADDRESS_TAGS = ("addr:housenumber", "addr:street", "addr:city")
_WEBSITE_TAGS = ("website", "contact:website")
_PHONE_TAGS = ("phone", "contact:phone")
_EMAIL_TAGS = ("email", "contact:email")
_BRAND_TAGS = ("brand", "brand:wikidata", "operator", "operator:wikidata")
_SOCIAL_TAGS = (
    "contact:instagram",
    "contact:facebook",
    "contact:tiktok",
    "contact:youtube",
)
_METADATA_TAGS = (
    "opening_hours",
    "sport",
    "internet_access",
    "wheelchair",
    "swimming_pool",
    "sauna",
    "shower",
)
_GYM_TAXONOMY_TAGS = {
    ("leisure", "fitness_centre"),
    ("amenity", "gym"),
}


def _count_present(tags: dict[str, object], keys: tuple[str, ...]) -> int:
    return sum(1 for key in keys if key in tags and str(tags[key]).strip())


def _has_any(tags: dict[str, object], keys: tuple[str, ...]) -> bool:
    return _count_present(tags, keys) > 0


def _gym_taxonomy_score(tags: dict[str, object]) -> float:
    for key, expected in _GYM_TAXONOMY_TAGS:
        if str(tags.get(key, "")).strip().lower() == expected:
            return 0.10
    return 0.0


def _address_score(tags: dict[str, object]) -> float:
    count = _count_present(tags, _ADDRESS_TAGS)
    if count == 3:
        return 0.22
    if count == 2:
        return 0.16
    if count == 1:
        return 0.08
    return 0.0


def _contact_score(tags: dict[str, object]) -> float:
    score = 0.0

    if _has_any(tags, _WEBSITE_TAGS):
        score += 0.22
    if _has_any(tags, _PHONE_TAGS):
        score += 0.10
    if _has_any(tags, _EMAIL_TAGS):
        score += 0.06
    if "opening_hours" in tags and str(tags["opening_hours"]).strip():
        score += 0.12

    if _has_any(tags, _WEBSITE_TAGS) and _has_any(tags, _PHONE_TAGS):
        score += 0.05
    if _has_any(tags, _WEBSITE_TAGS) and "opening_hours" in tags:
        score += 0.03

    return score


def _brand_score(tags: dict[str, object]) -> float:
    count = _count_present(tags, _BRAND_TAGS)
    if count >= 3:
        return 0.18
    if count == 2:
        return 0.14
    if count == 1:
        return 0.08
    return 0.0


def _metadata_score(tags: dict[str, object]) -> float:
    count = _count_present(tags, _METADATA_TAGS) + _count_present(tags, _SOCIAL_TAGS)
    return min(count * 0.02, 0.10)


def _name_score(gym: Gym) -> float:
    return 0.08 if gym.norm_name not in GENERIC_NAMES else 0.0


def _refs_score(gym: Gym) -> float:
    if len(gym.osm_refs) >= 3:
        return 0.18
    if len(gym.osm_refs) == 2:
        return 0.12
    return 0.0


def _external_validation_score(gym: Gym) -> float:
    provenance = gym.source_provenance or {}
    external_refs = provenance.get("external_refs")
    if not isinstance(external_refs, dict):
        return 0.0

    tomtom = external_refs.get("tomtom")
    if not isinstance(tomtom, dict):
        return 0.0

    status = str(tomtom.get("status") or provenance.get("match_status") or "")
    distance = tomtom.get("distance_m")
    url = tomtom.get("url")

    if status == "matched":
        score = 0.12
        if isinstance(distance, (int, float)):
            if distance <= 50:
                score += 0.06
            elif distance <= 150:
                score += 0.04
            else:
                score += 0.02
        if isinstance(url, str) and url.strip():
            score += 0.02
        return score

    if status == "name_mismatch":
        return 0.04

    return 0.0


def compute_confidence(gym: Gym) -> float:
    tags = gym.tags
    score = 0.0

    score += _gym_taxonomy_score(tags)
    score += _refs_score(gym)
    score += _address_score(tags)
    score += _contact_score(tags)
    score += _brand_score(tags)
    score += _metadata_score(tags)
    score += _name_score(gym)
    score += _external_validation_score(gym)

    gym.confidence_score = round(min(score, 1.0), 2)
    return gym.confidence_score
