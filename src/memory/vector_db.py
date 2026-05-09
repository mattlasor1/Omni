from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any
import numpy as np
import uuid

class SolidStateWiki:
    """
    Interface for the Qdrant Vector Database representing the long-term, 
    solid-state LLM wiki of the Digital Twin.
    """
    def __init__(self, host: str = "localhost", port: int = 6333, collection_name: str = "twin_memory"):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        self._ensure_collection_exists(vector_size=256) # Default size, matching extractor output

    def _ensure_collection_exists(self, vector_size: int):
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    def store_parameters(self, parameters: np.ndarray, metadata: Dict[str, Any] = None):
        """
        Stores a newly extracted or regressed parameter vector into the long-term memory.
        """
        point_id = str(uuid.uuid4())
        point = PointStruct(
            id=point_id,
            vector=parameters.tolist(),
            payload=metadata or {}
        )
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        return point_id

    def retrieve_similar(self, query_vector: np.ndarray, limit: int = 5) -> List[Any]:
        """
        Retrieves the most mathematically similar historical parameters.
        Used during the regression step to integrate new knowledge with existing context.
        """
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist(),
            limit=limit
        )
        return results
