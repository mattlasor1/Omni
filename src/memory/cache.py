import json
import redis
from typing import List, Dict, Any, Optional

class LivestreamCache:
    """
    Interface for the ultra-fast Redis cache to store incoming data streams.
    """
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.stream_key = "omnitwin:ingestion:stream"

    def add_to_stream(self, data: Dict[str, Any]) -> str:
        """
        Adds a raw data payload to the Redis stream.
        """
        # Redis XADD requires string values
        payload = {k: json.dumps(v) if not isinstance(v, str) else v for k, v in data.items()}
        message_id = self.client.xadd(self.stream_key, payload)
        return message_id

    def read_stream(self, count: int = 100) -> List[tuple]:
        """
        Reads pending messages from the stream for maintenance processing.
        """
        # Read from the beginning of the stream (or using a consumer group in production)
        messages = self.client.xread({self.stream_key: '0-0'}, count=count)
        return messages

    def acknowledge_and_delete(self, message_ids: List[str]):
        """
        Removes processed messages from the stream.
        """
        if message_ids:
            self.client.xdel(self.stream_key, *message_ids)
