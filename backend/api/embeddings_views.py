def serialize_gym_embedding_v2(gym: dict, *, region: str) -> dict:
    return {
        "id": gym["id"],
        "name": gym["name"],
        "region": region,
        "embedding_text": build_gym_embedding_text(gym),
        "inference": [
            {
                "key": k,
                "value": str(v.get("value")),
                "confidence": v.get("confidence"),
                "source": v.get("source"),
            }
            for k, v in gym["inference"].items()
        ],
        "confidence_score": gym.get("confidence_score"),
        "lat": gym.get("lat"),
        "lon": gym.get("lon"),
    }


def build_gym_embedding_text(gym: dict) -> str:
    """
    Deterministic, stable text representation of a gym.
    This string is what gets embedded.
    """
    parts: list[str] = []

    parts.append(f"Gym name: {gym['name']}")
    parts.append(f"Region: {gym.get('region')}")

    if gym.get("confidence_score") is not None:
        parts.append(f"Overall confidence score: {gym['confidence_score']}")

    inferred = gym.get("inference", {})

    for key, result in inferred.items():
        readable_key = key.replace("_", " ")

        value = result.get("value")
        confidence = result.get("confidence")


        parts.append(
            f"Inferred {readable_key}: {value} "
            f"(confidence {confidence})"
        )

    if summary := gym.get("inference_summary"):
        if isinstance(summary, dict):
            for k, v in summary.items():
                parts.append(f"{k}: {v}")

    return ". ".join(parts)

