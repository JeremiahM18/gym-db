def test_v2_embeddings_basic_shape(client, override_auth):
    resp = client.get("/v2/gyms/embeddings")
    assert resp.status_code == 200

    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0

    gym = data[0]

    # Core identity
    assert "id" in gym
    assert isinstance(gym["id"], str)

    assert "name" in gym
    assert isinstance(gym["name"], str)

    assert "region" in gym
    assert isinstance(gym["region"], str)

    # Embedding text
    assert "embedding_text" in gym
    assert isinstance(gym["embedding_text"], str)
    assert len(gym["embedding_text"]) > 0

    # Inference flattened
    assert "inference" in gym
    assert isinstance(gym["inference"], list)
    assert len(gym["inference"]) > 0

    inf = gym["inference"][0]
    assert "key" in inf
    assert "value" in inf
    assert "confidence" in inf
    assert "source" in inf

    assert isinstance(inf["key"], str)
    assert isinstance(inf["value"], str)
    assert isinstance(inf["confidence"], float)


def test_v2_embedding_text_is_deterministic(client, override_auth):
    resp1 = client.get("/v2/gyms/embeddings")
    resp2 = client.get("/v2/gyms/embeddings")

    gym1 = resp1.json()[0]
    gym2 = resp2.json()[0]

    assert gym1["embedding_text"] == gym2["embedding_text"]


def test_embedding_text_contains_inference(client, override_auth):
    resp = client.get("/v2/gyms/embeddings")
    gym = resp.json()[0]

    text = gym["embedding_text"].lower()

    # At least one inference keywork should appear
    found = any(
        inf["key"].replace("_", " ") in text
        for inf in gym["inference"]
    )

    assert found

