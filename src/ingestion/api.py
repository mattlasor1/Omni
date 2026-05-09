from fastapi import APIRouter, WebSocket, WebSocketDisconnect, BackgroundTasks
from pydantic import BaseModel
import time
from src.memory.cache import LivestreamCache

router = APIRouter()
cache = LivestreamCache(host="omnitwin-redis")

class TextPayload(BaseModel):
    source_id: str
    content: str
    context: dict = {}

@router.post("/ingest/text")
async def ingest_text(payload: TextPayload):
    """
    Ingests text data, packages it with timestamps, and dumps it straight into the fast cache.
    """
    data = {
        "type": "text",
        "source_id": payload.source_id,
        "content": payload.content,
        "context": payload.context,
        "timestamp": time.time()
    }
    msg_id = cache.add_to_stream(data)
    return {"status": "success", "message_id": msg_id}

@router.websocket("/ingest/visual/{source_id}")
async def ingest_visual_stream(websocket: WebSocket, source_id: str):
    """
    Accepts a stream of visual frames (e.g., base64 encoded images or raw bytes) 
    and caches them continuously.
    """
    await websocket.accept()
    try:
        while True:
            # Receive frame data
            data = await websocket.receive_text() # Assuming base64 or JSON for prototype
            
            # Immediately dump to cache
            payload = {
                "type": "visual_frame",
                "source_id": source_id,
                "content": data,
                "timestamp": time.time()
            }
            cache.add_to_stream(payload)
            
    except WebSocketDisconnect:
        print(f"Visual stream disconnected for source: {source_id}")
