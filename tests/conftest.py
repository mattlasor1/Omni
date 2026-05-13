import pytest
import os
import shutil
from types import SimpleNamespace

import numpy as np

os.environ["QDRANT_HOST"] = "localhost"
os.environ["REDIS_HOST"] = "localhost"
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "tmp_data")
if os.path.exists(TEST_DATA_DIR):
    shutil.rmtree(TEST_DATA_DIR)
os.environ["OMNI_DATA_DIR"] = TEST_DATA_DIR

# Mock out network calls during testing
@pytest.fixture(autouse=True)
def mock_qdrant(mocker):
    mocker.patch('src.memory.vector_db.SolidStateWiki._ensure_collection_exists', return_value=None)
    mocker.patch('qdrant_client.QdrantClient.__init__', return_value=None)

@pytest.fixture(autouse=True)
def mock_redis(mocker):
    mocker.patch('redis.Redis.__init__', return_value=None)

@pytest.fixture
def mock_generation_stack(mocker):
    import src.generation.api as gen_api

    mock_point = SimpleNamespace(
        id="mock_id",
        vector=np.ones(256, dtype=np.float32).tolist(),
        payload={
            "concept": "Mock Concept",
            "bayes_alpha": 2.0,
            "bayes_beta": 1.0,
            "fractal_depth": 1,
            "somatic_marker": 0.2,
        },
    )

    mock_wiki = mocker.MagicMock()
    mock_wiki.semantic_collection = "semantic_memory"
    mock_wiki.retrieve_similar.return_value = [mock_point]
    mock_wiki.store_semantic.return_value = "semantic-id"

    mock_cache = mocker.MagicMock()
    mock_cache.add_to_stream.return_value = "123-0"

    mock_extractor = mocker.MagicMock()
    mock_extractor.extract.return_value = np.ones(256, dtype=np.float32)

    mock_reasoning = mocker.MagicMock()
    mock_reasoning.client = None
    mock_reasoning.generate_response.return_value = "[Local Sovereign Response]"

    mock_dual_process = mocker.MagicMock()
    mock_dual_process.route_query.return_value = ("[Local Sovereign Response]", "System 2")

    mock_tom = mocker.MagicMock()
    mock_tom.model_audience.return_value = "Answer clearly."

    mock_daemon = mocker.MagicMock()
    mock_spatial = mocker.MagicMock()
    mock_neuroplasticity = mocker.MagicMock()
    mock_action_engine = mocker.MagicMock()
    mock_action_engine.decide_action.return_value = {"action": "none", "reason": "test"}
    mock_execution_router = mocker.MagicMock()
    mock_execution_router.execute_action.return_value = "Decided to take no action."
    mock_world_model = SimpleNamespace(
        mcts=mocker.MagicMock(
            find_golden_path=mocker.MagicMock(
                return_value={
                    "action": {"action": "none"},
                    "proceed": True,
                    "prediction": "MCTS path simulated",
                    "score": 1.0,
                    "simulations_run": 3,
                }
            )
        )
    )
    mock_authority = mocker.MagicMock()
    mock_authority.evaluate_authority.return_value = True

    assigned = {
        "wiki": mock_wiki,
        "cache": mock_cache,
        "extractor": mock_extractor,
        "reasoning": mock_reasoning,
        "dual_process": mock_dual_process,
        "tom": mock_tom,
        "daemon": mock_daemon,
        "spatial": mock_spatial,
        "neuroplasticity": mock_neuroplasticity,
        "action_engine": mock_action_engine,
        "execution_router": mock_execution_router,
        "world_model": mock_world_model,
        "authority": mock_authority,
    }

    for name, value in assigned.items():
        setattr(gen_api, name, value)

    yield gen_api

    for name in assigned:
        setattr(gen_api, name, None)
