from gymdb.domain.models import Gym
from gymdb.domain.scoring import compute_confidence


def make_gym(*, name: str, norm_name: str | None = None, tags: dict | None = None, refs: int = 1) -> Gym:
    return Gym(
        name=name,
        norm_name=norm_name or name.lower().replace(" ", "_"),
        lat=35.0,
        lon=-86.0,
        osm_refs=[{"type": "node", "id": index + 1} for index in range(refs)],
        tags=tags or {},
    )


def test_sparse_generic_gym_scores_low():
    gym = make_gym(
        name="Gym",
        norm_name="gym",
        tags={"leisure": "fitness_centre", "name": "Gym"},
    )

    score = compute_confidence(gym)

    assert score <= 0.12


def test_life_time_style_gym_scores_higher_with_brand_and_contact_surface():
    gym = make_gym(
        name="Life Time",
        norm_name="life_time",
        tags={
            "brand": "Life Time",
            "brand:wikidata": "Q6545004",
            "internet_access": "wlan",
            "leisure": "fitness_centre",
            "name": "Life Time",
            "opening_hours": "Mo-Fr 04:00-23:00; Sa,Su 05:00-21:00",
            "website": "https://www.lifetime.life/life-time-locations/tn-franklin.html",
        },
    )

    score = compute_confidence(gym)

    assert score >= 0.65


def test_ymca_style_gym_scores_higher_with_operator_and_contact_depth():
    gym = make_gym(
        name="Maryland Farms YMCA",
        norm_name="maryland_farms_ymca",
        tags={
            "addr:housenumber": "5101",
            "addr:street": "Maryland Way",
            "leisure": "fitness_centre",
            "name": "Maryland Farms YMCA",
            "operator": "YMCA of Middle Tennessee",
            "phone": "+1-615-373-2900",
            "website": "https://www.ymcamidtn.org/maryland-farms",
        },
    )

    score = compute_confidence(gym)

    assert score >= 0.7


def test_multiple_osm_refs_increase_confidence():
    sparse = make_gym(
        name="CrossFit Example",
        tags={"leisure": "fitness_centre", "name": "CrossFit Example"},
        refs=1,
    )
    richer = make_gym(
        name="CrossFit Example",
        tags={"leisure": "fitness_centre", "name": "CrossFit Example"},
        refs=3,
    )

    assert compute_confidence(richer) > compute_confidence(sparse)
