import pytest
import os

os.environ["QDRANT_HOST"] = "localhost"
os.environ["REDIS_HOST"] = "localhost"

# Mock out network calls during testing
@pytest.fixture(autouse=True)
def mock_qdrant(mocker):
    mocker.patch('src.memory.vector_db.SolidStateWiki._ensure_collection_exists', return_value=None)
    mocker.patch('qdrant_client.QdrantClient.__init__', return_value=None)

@pytest.fixture(autouse=True)
def mock_redis(mocker):
    mocker.patch('redis.Redis.__init__', return_value=None)
