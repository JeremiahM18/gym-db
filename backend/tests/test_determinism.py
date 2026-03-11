import copy

def test_inference_is_deterministic(gym_factory, infer):
    gym = gym_factory({"opening_hours": "24/7"})

    infer(gym)
    first = copy.deepcopy(gym.inferred)

    infer(gym)
    assert gym.inferred == first

