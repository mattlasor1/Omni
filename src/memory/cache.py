from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict, List

import redis

from src.runtime import get_settings


class LocalRedisClient:
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
        return {"streams": {}, "kv": {}, "seq": {}}

    def _save(self) -> None:
        with self.state_path.open("w", encoding="utf-8") as handle:
            json.dump(self._state, handle, indent=2)

    def xadd(self, stream_key: str, payload: Dict[str, Any]) -> str:
        with self._lock:
            seq = self._state["seq"].get(stream_key, 0) + 1
            self._state["seq"][stream_key] = seq
            message_id = f"{seq}-0"
            stream = self._state["streams"].setdefault(stream_key, [])
            stream.append({"id": message_id, "payload": payload})
            self._save()
        return message_id

    def xread(self, stream_map: Dict[str, str], count: int = 100) -> List[tuple]:
        results = []
        for stream_key in stream_map:
            stream = self._state["streams"].get(stream_key, [])
            messages = [(entry["id"], entry["payload"]) for entry in stream[:count]]
            if messages:
                results.append((stream_key, messages))
        return results

    def xdel(self, stream_key: str, *message_ids: str) -> int:
        with self._lock:
            stream = self._state["streams"].get(stream_key, [])
            before = len(stream)
            self._state["streams"][stream_key] = [entry for entry in stream if entry["id"] not in message_ids]
            removed = before - len(self._state["streams"][stream_key])
            self._save()
        return removed

    def xinfo_stream(self, stream_key: str) -> Dict[str, int]:
        return {"length": len(self._state["streams"].get(stream_key, []))}

    def get(self, key: str) -> Any:
        return self._state["kv"].get(key)

    def set(self, key: str, value: Any) -> bool:
        with self._lock:
            self._state["kv"][key] = value
            self._save()
        return True

    def incr(self, key: str) -> int:
        return self.incrby(key, 1)

    def incrby(self, key: str, amount: int) -> int:
        with self._lock:
            current = int(self._state["kv"].get(key, 0) or 0)
            current += amount
            self._state["kv"][key] = current
            self._save()
        return current

    def ping(self) -> bool:
        return True


class LivestreamCache:
    """
    Interface for the ultra-fast cache to store incoming data streams.
    Falls back to a local JSON-backed stream when Redis is unavailable so the
    desktop app can run offline without companion services.
    """

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.stream_key = "omnitwin:ingestion:stream"
        self._settings = get_settings()
        self.client = self._create_client(host=host, port=port, db=db)

    def _create_client(self, host: str, port: int, db: int):
        try:
            client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            if client is None or not hasattr(client, "ping"):
                raise RuntimeError("Redis client unavailable")
            client.ping()
            return client
        except Exception:
            return LocalRedisClient(self._settings.cache_store_path)

    def add_to_stream(self, data: Dict[str, Any]) -> str:
        payload = {k: json.dumps(v) if not isinstance(v, str) else v for k, v in data.items()}
        return self.client.xadd(self.stream_key, payload)

    def read_stream(self, count: int = 100) -> List[tuple]:
        return self.client.xread({self.stream_key: "0-0"}, count=count)

    def acknowledge_and_delete(self, message_ids: List[str]):
        if message_ids:
            self.client.xdel(self.stream_key, *message_ids)
