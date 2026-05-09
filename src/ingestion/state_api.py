import os
from fastapi import APIRouter
from src.memory.cache import LivestreamCache
from src.memory.vector_db import SolidStateWiki

router = APIRouter()
cache = None
wiki = None

def get_cache():
    global cache
    if cache is None:
        cache = LivestreamCache(host=os.getenv("REDIS_HOST", "localhost"))
    return cache

def get_wiki():
    global wiki
    if wiki is None:
        wiki = SolidStateWiki(host=os.getenv("QDRANT_HOST", "localhost"))
    return wiki

@router.get("/state")
async def get_system_state():
    try:
        stream_info = get_cache().client.xinfo_stream(get_cache().stream_key)
        cache_len = stream_info.get('length', 0)
    except:
        cache_len = 0

    try:
        ep_info = get_wiki().client.get_collection(get_wiki().episodic_collection)
        episodic_count = ep_info.points_count
    except:
        episodic_count = 0
        
    try:
        sem_info = get_wiki().client.get_collection(get_wiki().semantic_collection)
        semantic_count = sem_info.points_count
    except:
        semantic_count = 0

    return {
        "status": "online",
        "cache_length": cache_len,
        "episodic_points": episodic_count,
        "semantic_points": semantic_count
    }

# Endpoint to trigger reflection manually from UI for demo purposes
@router.post("/maintenance/reflect")
async def trigger_reflection():
    try:
        from src.maintenance.tasks import autonomous_reflection, process_cache_to_memory
        # Process cache first
        process_cache_to_memory.delay()
        # Trigger reflection
        autonomous_reflection.delay()
        return {"status": "success", "message": "Reflection loop triggered in background."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
