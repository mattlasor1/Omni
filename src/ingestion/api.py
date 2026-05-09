import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, BackgroundTasks
from pydantic import BaseModel
import time
from src.memory.cache import LivestreamCache

router = APIRouter()
cache = None

def get_cache():
    global cache
    if cache is None:
        cache = LivestreamCache(host=os.getenv("REDIS_HOST", "localhost"))
    return cache

class TextPayload(BaseModel):
    source_id: str
    content: str
    context: dict = {}

@router.post("/ingest/text")
async def ingest_text(payload: TextPayload):
    data = {
        "type": "text",
        "source_id": payload.source_id,
        "content": payload.content,
        "context": payload.context,
        "timestamp": time.time()
    }
    msg_id = get_cache().add_to_stream(data)
    return {"status": "success", "message_id": msg_id}

@router.websocket("/ingest/visual/{source_id}")
async def ingest_visual_stream(websocket: WebSocket, source_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text() 
            payload = {
                "type": "visual_frame",
                "source_id": source_id,
                "content": data,
                "timestamp": time.time()
            }
            get_cache().add_to_stream(payload)
    except WebSocketDisconnect:
        print(f"Visual stream disconnected for source: {source_id}")
