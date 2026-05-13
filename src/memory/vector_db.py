from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from src.runtime import get_settings


@dataclass
class LocalPoint:
    id: str
    vector: List[float]
    payload: Dict[str, Any]
    score: float = 0.0


class LocalVectorClient:
    def __init__(self, state_path: Path):
        self.state_path = state_path
        self._lock = threading.Lock()
        self._state = self._load()

    def _load(self) -> dict:
        if self.state_path.exists():
            try:
                with self.state_path.open("r", encoding="utf-8") as handle:
                    return json.load(handle)
            except json.JSONDecodeError:
                pass
        return {}

    def _save(self) -> None:
        with self.state_path.open("w", encoding="utf-8") as handle:
            json.dump(self._state, handle, indent=2)

    def get_collections(self):
        collections = [SimpleNamespace(name=name) for name in self._state.keys()]
        return SimpleNamespace(collections=collections)

    def create_collection(self, collection_name: str, vectors_config: VectorParams):
        with self._lock:
            self._state.setdefault(
                collection_name,
                {"vector_size": vectors_config.size, "points": []},
            )
            self._save()

    def get_collection(self, collection_name: str):
        collection = self._state.get(collection_name, {"points": []})
        return SimpleNamespace(points_count=len(collection["points"]))

    def upsert(self, collection_name: str, points: List[PointStruct]):
        with self._lock:
            collection = self._state.setdefault(collection_name, {"vector_size": 256, "points": []})
            indexed = {point["id"]: point for point in collection["points"]}
            for point in points:
                point_id = str(getattr(point, "id"))
                indexed[point_id] = {
                    "id": point_id,
                    "vector": list(getattr(point, "vector")),
                    "payload": dict(getattr(point, "payload", {}) or {}),
                }
            collection["points"] = list(indexed.values())
            self._save()

    def search(self, collection_name: str, query_vector: List[float], limit: int = 5, score_threshold: float = 0.0):
        collection = self._state.get(collection_name, {"points": []})
        query = np.array(query_vector, dtype=np.float32)
        query_norm = np.linalg.norm(query) or 1.0
        results = []
        for point in collection["points"]:
            vector = np.array(point["vector"], dtype=np.float32)
            vector_norm = np.linalg.norm(vector) or 1.0
            score = float(np.dot(query, vector) / (query_norm * vector_norm))
            if score >= score_threshold:
                results.append(
                    LocalPoint(
                        id=point["id"],
                        vector=point["vector"],
                        payload=point.get("payload", {}),
                        score=score,
                    )
                )
        results.sort(key=lambda item: item.score, reverse=True)
        return results[:limit]

    def scroll(self, collection_name: str, limit: int = 1000, with_vectors: bool = False, with_payload: bool = False):
        collection = self._state.get(collection_name, {"points": []})
        points = []
        for point in collection["points"][:limit]:
            points.append(
                LocalPoint(
                    id=point["id"],
                    vector=point["vector"] if with_vectors or True else [],
                    payload=point.get("payload", {}) if with_payload or True else {},
                )
            )
        return points, None

    def delete(self, collection_name: str, points_selector):
        with self._lock:
            collection = self._state.get(collection_name, {"points": []})
            ids = {str(point_id) for point_id in points_selector}
            collection["points"] = [point for point in collection["points"] if point["id"] not in ids]
            self._save()

    def set_payload(self, collection_name: str, payload: Dict[str, Any], points: List[str]):
        with self._lock:
            collection = self._state.get(collection_name, {"points": []})
            point_ids = {str(point_id) for point_id in points}
            for point in collection["points"]:
                if point["id"] in point_ids:
                    point["payload"] = dict(payload)
            self._save()


class SolidStateWiki:
    """
    Hierarchical Vector Database representing the digital twin's memory.
    Falls back to a local JSON store when Qdrant is unavailable.
    """

    def __init__(self, host: str = "localhost", port: int = 6333):
        self._settings = get_settings()
        self.client = self._create_client(host=host, port=port)
        self.episodic_collection = "episodic_memory"
        self.semantic_collection = "semantic_memory"
        self._ensure_collection_exists(self.episodic_collection, vector_size=256)
        self._ensure_collection_exists(self.semantic_collection, vector_size=256)

    def _create_client(self, host: str, port: int):
        try:
            client = QdrantClient(host=host, port=port, check_compatibility=False)
            if client is None or not hasattr(client, "get_collections"):
                raise RuntimeError("Qdrant client unavailable")
            client.get_collections()
            return client
        except Exception:
            return LocalVectorClient(self._settings.vector_store_path)

    def _ensure_collection_exists(self, collection_name: str, vector_size: int):
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)
            if not exists:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )
        except Exception as exc:
            print(f"Warning: Could not connect to vector store for {collection_name}: {exc}")

    def store_episodic(self, parameters: np.ndarray, metadata: Dict[str, Any] = None) -> str:
        point_id = str(uuid.uuid4())
        point = PointStruct(id=point_id, vector=parameters.tolist(), payload=metadata or {})
        self.client.upsert(collection_name=self.episodic_collection, points=[point])
        return point_id

    def store_semantic(self, parameters: np.ndarray, metadata: Dict[str, Any] = None, point_id: str = None) -> str:
        if point_id is None:
            point_id = str(uuid.uuid4())
        payload = metadata or {}
        payload.setdefault("bayes_alpha", 1.0)
        payload.setdefault("bayes_beta", 1.0)
        payload.setdefault("fractal_depth", 0)
        point = PointStruct(id=point_id, vector=parameters.tolist(), payload=payload)
        self.client.upsert(collection_name=self.semantic_collection, points=[point])
        return point_id

    def retrieve_similar(self, query_vector: np.ndarray, collection: str, limit: int = 5, min_score: float = 0.0) -> List[Any]:
        return self.client.search(
            collection_name=collection,
            query_vector=query_vector.tolist(),
            limit=limit,
            score_threshold=min_score,
        )

    def fetch_all_episodic(self, limit: int = 1000) -> tuple[List[np.ndarray], List[Dict[str, Any]]]:
        points = self.client.scroll(
            collection_name=self.episodic_collection,
            limit=limit,
            with_vectors=True,
        )[0]
        vectors = [np.array(point.vector) for point in points]
        payloads = [point.payload for point in points]
        return vectors, payloads
