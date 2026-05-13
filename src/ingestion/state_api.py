import os
from fastapi import APIRouter
from src.memory.cache import LivestreamCache
from src.memory.vector_db import SolidStateWiki
from src.learning.state import InternalStateEngine
from src.maintenance.circadian import CircadianEngine
from src.training.service import TrainingService
from src.runtime import get_settings

router = APIRouter()
cache = None
wiki = None
state_engine = None
circadian_engine = None
training_service = TrainingService()
settings = get_settings()

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

def get_state_engines():
    global state_engine, circadian_engine
    if state_engine is None:
        state_engine = InternalStateEngine()
        circadian_engine = CircadianEngine()
    return state_engine, circadian_engine

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
        
        # Pull a sample to get average epistemic uncertainty and fractal depth
        sample = get_wiki().client.scroll(collection_name=get_wiki().semantic_collection, limit=100, with_payload=True)[0]
        avg_uncertainty = 0.0
        avg_depth = 0.0
        if sample:
            from src.learning.epistemology import BayesianEngine
            bayes = BayesianEngine()
            unc_sum = 0.0
            depth_sum = 0.0
            for p in sample:
                a = p.payload.get("bayes_alpha", 1.0)
                b = p.payload.get("bayes_beta", 1.0)
                unc_sum += bayes.calculate_uncertainty(a, b)
                depth_sum += p.payload.get("fractal_depth", 0)
            avg_uncertainty = unc_sum / len(sample)
            avg_depth = depth_sum / len(sample)
    except:
        semantic_count = 0
        avg_uncertainty = 0.0
        avg_depth = 0.0

    se, ce = get_state_engines()
    se.update_stress(cache_len) # Live update stress based on queue
    ce.tick()
    state_summary = se.get_state_summary()
    
    # Fetch Exponential Growth Metrics
    try:
        self_play_count = int(get_cache().client.get("omnitwin:metrics:self_play_count") or 0)
        epiphanies = int(get_cache().client.get("omnitwin:metrics:epiphanies") or 0)
        seeker_dispatches = int(get_cache().client.get("omnitwin:metrics:seeker_dispatches") or 0)
        
        # Fetch Thalamic and Entropy metrics
        thalamic_ratio = float(get_cache().client.get("omnitwin:metrics:thalamic_filter_ratio") or 0.0)
        pruned_count = int(get_cache().client.get("omnitwin:metrics:memories_pruned") or 0)
        
        axioms_compressed = int(get_cache().client.get("omnitwin:metrics:axioms_compressed") or 0)
        prime_directive = get_cache().client.get("omnitwin:metrics:prime_directive") or ""
        # Fetch Omega Convergence
        omega = float(get_cache().client.get("omnitwin:metrics:omega_convergence") or 0.0)
    except:
        self_play_count = 0
        epiphanies = 0
        seeker_dispatches = 0
        axioms_compressed = 0
        prime_directive = ""
        thalamic_ratio = 0.0
        pruned_count = 0
        omega = 0.0
    
    return {
        "status": "online",
        "offline_mode": settings.offline_strict,
        "cache_length": cache_len,
        "episodic_points": episodic_count,
        "semantic_points": semantic_count,
        "avg_uncertainty": round(avg_uncertainty, 4),
        "avg_fractal_depth": round(avg_depth, 2),
        "emotional_state": state_summary,
        "biological_state": ce.state,
        "energy": round(ce.energy, 1),
        "prime_directive": prime_directive,
        "exponential_metrics": {
            "self_play_count": self_play_count,
            "epiphanies": epiphanies,
            "seeker_dispatches": seeker_dispatches,
            "axioms_compressed": axioms_compressed
        },
        "philosophical_metrics": {
            "thalamic_ratio": round(thalamic_ratio, 2),
            "pruned_count": pruned_count,
            "theodicy_resolutions": 0, # Could wire to real stats if cached
            "omega_convergence": omega
        },
        "training": {
            "profile": training_service.get_active_profile(),
            "evaluation": training_service.evaluate_readiness(persist=False) if training_service.get_active_profile() else {"status": "unconfigured", "readiness_score": 0.0},
        },
    }

@router.get("/logos")
async def get_logos_stream():
    """
    Fetches spontaneous philosophical insights published by the Twin.
    """
    try:
        messages = get_cache().client.xread({"omnitwin:logos:stream": "0-0"}, count=5)
        insights = []
        msg_ids = []
        if messages:
            for stream_name, stream_messages in messages:
                for msg_id, payload in stream_messages:
                    insights.append(payload.get("insight", ""))
                    msg_ids.append(msg_id)
            get_cache().client.xdel("omnitwin:logos:stream", *msg_ids)
        return {"insights": insights}
    except Exception as e:
        return {"insights": []}

@router.get("/prophecy")
async def get_prophecy_stream():
    """
    Fetches Cassandra deep-time predictions.
    """
    try:
        messages = get_cache().client.xread({"omnitwin:prophecy:stream": "0-0"}, count=5)
        prophecies = []
        msg_ids = []
        if messages:
            for stream_name, stream_messages in messages:
                for msg_id, payload in stream_messages:
                    prophecies.append(payload.get("prophecy", ""))
                    msg_ids.append(msg_id)
            get_cache().client.xdel("omnitwin:prophecy:stream", *msg_ids)
        return {"prophecies": prophecies}
    except Exception as e:
        return {"prophecies": []}

@router.post("/maintenance/nemesis")
async def trigger_nemesis_strike():
    try:
        from src.maintenance.tasks import trigger_nemesis
        trigger_nemesis.delay()
        return {"status": "success", "message": "Nemesis strike triggered."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/maintenance/growth")
async def trigger_exponential_growth():
    try:
        from src.maintenance.tasks import exponential_growth_cycle
        exponential_growth_cycle.delay()
        return {"status": "success", "message": "Exponential Growth cycle (Self-Play & Pollination) triggered."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/curiosity")
async def get_curiosity_stream():
    """
    Fetches pending curiosity questions generated by the Twin.
    """
    try:
        messages = get_cache().client.xread({"omnitwin:curiosity:stream": "0-0"}, count=5)
        questions = []
        msg_ids = []
        if messages:
            for stream_name, stream_messages in messages:
                for msg_id, payload in stream_messages:
                    questions.append(payload.get("question", ""))
                    msg_ids.append(msg_id)
                    
            # Auto-clear read questions for the demo
            get_cache().client.xdel("omnitwin:curiosity:stream", *msg_ids)
            
        return {"questions": questions}
    except Exception as e:
        return {"questions": []}

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
