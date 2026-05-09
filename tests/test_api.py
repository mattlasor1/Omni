import pytest
from fastapi.testclient import TestClient
from src.main import app
import json

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_ui_dashboard_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert b"OmniTwin Dashboard" in response.content

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
