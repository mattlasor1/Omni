from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_state_endpoint_degrades_without_services(mocker):
    mock_cache = mocker.MagicMock()
    mock_cache.stream_key = "omnitwin:ingestion:stream"
    mock_cache.client.xinfo_stream.side_effect = RuntimeError("redis unavailable")
    mock_cache.client.get.return_value = None

    mock_wiki = mocker.MagicMock()
    mock_wiki.episodic_collection = "episodic_memory"
    mock_wiki.semantic_collection = "semantic_memory"
    mock_wiki.client.get_collection.side_effect = RuntimeError("qdrant unavailable")

    mocker.patch("src.ingestion.state_api.get_cache", return_value=mock_cache)
    mocker.patch("src.ingestion.state_api.get_wiki", return_value=mock_wiki)

    response = client.get("/api/v1/state")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["cache_length"] == 0
    assert data["episodic_points"] == 0
    assert data["semantic_points"] == 0
    assert data["exponential_metrics"]["axioms_compressed"] == 0


def test_swarm_status_endpoint_smoke():
    response = client.get("/api/v1/swarm/status")

    assert response.status_code == 200
    data = response.json()
    assert data["node_id"]
    assert isinstance(data["peers"], list)
    assert isinstance(data["entangled_nodes"], int)
    assert isinstance(data["resonance_signature"], list)
