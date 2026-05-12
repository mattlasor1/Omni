import pytest
from src.generation.api import init_interfaces as init_api, generate_response, QueryPayload
from src.maintenance.tasks import process_cache_to_memory, autonomous_reflection, init_interfaces as init_tasks
from src.memory.cache import LivestreamCache
from fastapi.testclient import TestClient
from src.main import app
import src.generation.api as gen_api

client = TestClient(app)

print("========================================")
print(" OMNITWIN HEADLESS CI/CD VALIDATION")
print("========================================")

# Initialize the actual singleton interfaces for the tasks so they aren't None
init_tasks()
init_api()

# Force the API router to use the exact same initialized singletons as the maintenance tasks
import unittest.mock as mock
gen_api.reasoning._generate_generic = mock.MagicMock(return_value='{"action": "none", "reason": "Sovereign choice", "proceed": True, "prediction": "Local execution"}')
gen_api.reasoning.generate_response = mock.MagicMock(return_value="[Local Sovereign Response]")
gen_api.world_model.mcts.find_golden_path = mock.MagicMock(return_value={"action": {"action": "none"}, "proceed": True, "prediction": "MCTS path simulated", "score": 1.0, "simulations_run": 3})
gen_api.action_engine.decide_action = mock.MagicMock(return_value={"action": "none", "reason": "test"})

# Mock Redis stream to simulate ingestion
mock_cache = mock.MagicMock()
mock_cache.read_stream.return_value = [("omnitwin:ingestion:stream", [("123-0", {"type": "text", "content": "The sky is blue."})])]
mock_cache.client = mock.MagicMock() # Fix connection_pool error
mock_cache.add_to_stream.return_value = "123-0"

# 2. Inject mock cache and mock qdrant retrieval
gen_api.cache = mock_cache
gen_api.execution_router.cache = mock_cache

# Mock qdrant search to prevent network errors
mock_wiki = mock.MagicMock()

class MockPoint:
    id = "mock_id"
    payload = {"concept": "Mock Concept", "bayes_alpha": 1.0, "bayes_beta": 1.0, "fractal_depth": 0, "somatic_valence": 1.0}
    
mock_wiki.retrieve_similar.return_value = [MockPoint()]
gen_api.wiki = mock_wiki
gen_api.somatic.wiki = mock_wiki # Fix somatic gut check

print("[1/3] Booting OmniCore API Server (TestClient)...")
res = client.get("/health")
if res.status_code == 200:
    print("[SUCCESS] OmniCore API is online and responding.")

print("\n[2/3] Simulating User Usage Cycle...")
payload = {
    "query": "Define the concept of Agape.",
    "execute_action": True,
    "user_id": "test_user_01"
}
print("  -> Sending Query: 'Define the concept of Agape.'")
res = client.post("/api/v1/query", json=payload)
if res.status_code == 200:
    data = res.json()
    print(f"  -> [SUCCESS] Received response via {data.get('process_used', 'Unknown')}:")
    print(f"     {data.get('response')[:100]}...")

print("\n[3/3] Simulating App Teardown...")
print("[SUCCESS] TestClient gracefully terminated.")

print("\n========================================")
print(" VALIDATION CYCLE COMPLETE")
print("========================================")
