import os
from fastapi import APIRouter
from src.memory.cache import LivestreamCache
from src.memory.vector_db import SolidStateWiki

router = APIRouter()
# Defer initialization to avoid hitting network on import
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
    """
    Returns the current state of the caching and memory layers.
    """
    try:
        # Get pending messages in cache
        stream_info = get_cache().client.xinfo_stream(get_cache().stream_key)
        cache_len = stream_info.get('length', 0)
    except:
        cache_len = 0

    try:
        # Get count of points in Qdrant
        collection_info = get_wiki().client.get_collection(get_wiki().collection_name)
        vector_count = collection_info.points_count
    except:
        vector_count = 0

    return {
        "status": "online",
        "cache_length": cache_len,
        "memory_points": vector_count
    }
