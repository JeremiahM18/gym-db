from gymdb.domain.models import Gym

GENERIC_NAMES = {
    "gym",
    "fitness",
    "fitness center",
    "fitness centre",
    "health club",
}

def compute_confidence(gym: Gym) -> float:
    score = 0.0
    tags = gym.tags

    if len(gym.osm_refs) > 1:
        score += 0.20

    if any(k in tags for k in ("addr:housenumber", "addr:street", "addr:city")):
        score += 0.20

    if "website" in tags or "contact:website" in tags:
        score += 0.30

    if "phone" in tags or "contact:phone" in tags:
        score += 0.10

    if "opening_hours" in tags:
        score += 0.10

    if gym.norm_name not in GENERIC_NAMES:
        score += 0.10

    gym.confidence_score = round(min(score, 1.0), 2)
    return gym.confidence_score

