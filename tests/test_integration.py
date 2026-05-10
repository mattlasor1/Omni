import pytest
from src.generation.api import init_interfaces as init_api, generate_response, QueryPayload
from src.maintenance.tasks import process_cache_to_memory, autonomous_reflection, init_interfaces as init_tasks
from src.memory.cache import LivestreamCache
from fastapi.testclient import TestClient
from src.main import app
import src.generation.api as gen_api
import src.generation.dual_process as dp

client = TestClient(app)

def test_full_sovereign_loop(mocker):
    init_api()
    init_tasks()

    # 1. Mock the local HuggingFace inference so test runs fast
    mocker.patch('src.learning.reasoning.CognitiveReasoningEngine._generate_generic', return_value='[Local Sovereign Response]')
    mocker.patch('src.learning.reasoning.CognitiveReasoningEngine.generate_response', return_value="[Local Sovereign Response]")
    mocker.patch('src.learning.mcts.MultiTimelineMCTS.find_golden_path', return_value={"action": {"action": "none"}, "proceed": True, "prediction": "MCTS path simulated", "score": 1.0, "simulations_run": 3})
    mocker.patch('src.generation.action.ProceduralActionEngine.decide_action', return_value={"action": "none", "reason": "test"})
    
    # Mock Redis stream to simulate ingestion
    mock_cache = mocker.MagicMock()
    mock_cache.read_stream.return_value = [("omnitwin:ingestion:stream", [("123-0", {"type": "text", "content": "The sky is blue."})])]
    mock_cache.client = mocker.MagicMock() # Fix connection_pool error
    mock_cache.add_to_stream.return_value = "123-0"
    
    # 2. Inject mock cache and mock qdrant retrieval
    mocker.patch('src.maintenance.tasks.cache', mock_cache)
    mocker.patch('src.generation.api.cache', mock_cache)
    gen_api.cache = mock_cache
    gen_api.execution_router.cache = mock_cache
    
    # Mock qdrant search to prevent network errors
    mock_wiki = mocker.MagicMock()
    
    class MockPoint:
        id = "mock_id"
        payload = {"concept": "Mock Concept", "bayes_alpha": 1.0, "bayes_beta": 1.0, "fractal_depth": 0, "somatic_valence": 1.0}
        
    mock_wiki.retrieve_similar.return_value = [MockPoint()]
    mocker.patch('src.generation.api.wiki', mock_wiki)
    mocker.patch('src.maintenance.tasks.wiki', mock_wiki)
    gen_api.wiki = mock_wiki
    gen_api.somatic.wiki = mock_wiki # Fix somatic gut check
    
    # 3. Simulate Maintenance Worker (Thalamic Gate -> Memory)
    res = process_cache_to_memory(batch_size=1)
    assert "Processed" in res or "Asleep" in res or "paused" in res
    
    # 4. Simulate Generation Query (Dual Process -> Moral Matrix -> MCTS)
    payload = {
        "query": "Is the sky blue?",
        "execute_action": True,
        "spatial_coords": [10.0, 15.0, 20.0]
    }
    
    resp = client.post("/api/v1/query", json=payload)
    
    assert resp.status_code == 200
    data = resp.json()
    assert "query" in data
    assert "response" in data
    assert "[Local Sovereign Response]" in data["response"] or "VETOED" in data["response"] or "System 1" in data.get("process_used", "")

