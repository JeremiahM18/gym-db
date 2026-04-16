from gymdb.gyms.queries import list_gyms


def _infer(gym: dict, key: str):
    for field in ("inferred", "inference"):
        item = gym.get(field, {}).get(key)
        if item is not None:
            return item.get("value") if isinstance(item, dict) else item
    return None


class StubStore:
    default_region = "test"

    def __init__(self, gyms: list[dict]):
        self._gyms = gyms

    def filter(self, *, region, min_conf=None, tier=None, specialty=None,
               lifter_friendly=None, is_24_7=None, limit=100, offset=0):
        results = list(self._gyms)
        if tier is not None:
            results = [g for g in results if _infer(g, "tier") == tier]
        if specialty is not None:
            results = [g for g in results if _infer(g, "specialty") == specialty]
        if lifter_friendly is not None:
            results = [g for g in results if _infer(g, "lifter_friendly") == lifter_friendly]
        if is_24_7 is not None:
            results = [g for g in results if _infer(g, "is_24_7") == is_24_7]
        return results[offset : offset + limit]

    def nearby(self, *, region, lat, lon, radius_m, min_conf=None, tier=None,
               specialty=None, lifter_friendly=None, is_24_7=None, limit=100, offset=0):
        if radius_m < 1_000:
            return [gym for gym in self._gyms if gym["lat"] == lat]
        return list(self._gyms)

    def get_by_id(self, region: str, gym_id: str):
        for gym in self._gyms:
            if gym["id"] == gym_id:
                return gym
        return None


def test_list_gyms_filters_by_tier_lifter_and_specialty():
    store = StubStore(
        [
            {
                "id": "premium-a",
                "lat": 36.16,
                "lon": -86.78,
                "inferred": {
                    "tier": {"value": "premium"},
                    "lifter_friendly": {"value": True},
                    "specialty": {"value": "powerlifting"},
                },
            },
            {
                "id": "basic-b",
                "lat": 36.17,
                "lon": -86.79,
                "inferred": {
                    "tier": {"value": "basic"},
                    "lifter_friendly": {"value": False},
                    "specialty": {"value": "general_fitness"},
                },
            },
        ]
    )

    results = list_gyms(
        store=store,
        region="test",
        tier="premium",
        specialty="powerlifting",
        lifter_friendly=True,
    )

    assert [gym["id"] for gym in results] == ["premium-a"]


def test_list_gyms_radius_filter_uses_store_nearby_candidates():
    store = StubStore(
        [
            {
                "id": "nearby",
                "lat": 36.1627,
                "lon": -86.7816,
                "inferred": {},
            },
            {
                "id": "far-away",
                "lat": 36.2627,
                "lon": -86.7816,
                "inferred": {},
            },
        ]
    )

    results = list_gyms(
        store=store,
        region="test",
        lat=36.1627,
        lon=-86.7816,
        radius_m=500,
    )

    assert [gym["id"] for gym in results] == ["nearby"]
