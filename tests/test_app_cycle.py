from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_headless_query_cycle(mock_generation_stack):
    response = client.post("/api/v1/query", json={
        "query": "Define the concept of Agape.",
        "execute_action": True,
        "user_id": "test_user_01",
    })

    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "[Local Sovereign Response]"
    assert data["action_decided"]["action"] == "none"
    assert data["mcts_simulation"] == "MCTS path simulated"
    assert data["action_result"] == "Decided to take no action."
