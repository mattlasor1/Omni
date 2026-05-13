import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_ui_dashboard_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert b"OmniTwin Backend Online" in response.content

def test_ingest_text_endpoint(mocker):
    # Mock redis cache to avoid requiring real redis during unit tests
    mock_cache = mocker.MagicMock()
    mock_cache.add_to_stream.return_value = "12345-0"
    mocker.patch('src.ingestion.api.get_cache', return_value=mock_cache)
    
    payload = {
        "source_id": "test_script",
        "content": "This is a test signal."
    }
    
    response = client.post("/api/v1/ingest/text", json=payload)
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_cache.add_to_stream.assert_called_once()

def test_query_json_endpoint(mock_generation_stack):
    response = client.post("/api/v1/query", json={
        "query": "What do you know?",
        "execute_action": False,
    })

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "What do you know?"
    assert data["response"] == "[Local Sovereign Response]"
    assert data["context_ids"] == ["mock_id"]
    assert data["process_used"] == "System 2"

def test_query_stream_endpoint(mock_generation_stack):
    response = client.post("/api/v1/query/stream", json={
        "query": "Stream a thought",
        "execute_action": False,
    })

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "Parameterizing Query" in response.text
    assert '"event": "complete"' in response.text
