import os
import uuid
import json
import asyncio
import time
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.memory.vector_db import SolidStateWiki
from src.learning.engine import ParameterExtractor
from src.learning.reasoning import CognitiveReasoningEngine
from src.learning.reinforcement import ReinforcementEngine
from src.generation.action import ProceduralActionEngine
from src.execution.tools import ExecutionRouter
from src.execution.meta_learning import MetaLearningEngine
from src.execution.self_modification import RecursiveSelfModificationEngine
from src.learning.world_model import PredictiveWorldModel
from src.memory.graph_db import CausalGraphMemory
from src.memory.spatial_db import SpatialMemoryManifold
from src.learning.morality import MoralAlignmentMatrix
from src.memory.cache import LivestreamCache
from src.learning.somatic import SomaticMarkerEngine
from src.learning.theory_of_mind import TheoryOfMindEngine
from src.generation.dual_process import DualProcessRouter
from src.learning.flashbulb import FlashbulbMemoryProtocol
from src.learning.state import InternalStateEngine
from src.learning.neuroplasticity import DynamicTopologyEngine
from src.learning.mirroring import EpisodicMirroringEngine
from src.generation.coprocessing import SymbioticCoProcessingEngine
from src.learning.stylometrics import StylometricEngine
from src.execution.authority import TrustAndAuthorityProtocol
from src.maintenance.circadian import PerpetualCognitiveDaemon
from src.swarm.omnipresence import ZeroConfigSwarm
from src.training.service import TrainingService
from src.runtime import get_settings

router = APIRouter()

# Defer initialization
wiki = None
cache = None
extractor = None
reasoning = None
rl_engine = None
action_engine = None
execution_router = None
world_model = None
graph = None
spatial = None
somatic = None
tom = None
dual_process = None
flashbulb = None
state = None
morality = None
self_mod = None
neuroplasticity = None
mirroring = None
coprocessing = None
stylometrics = None
authority = None
daemon = None
swarm = None
training = None
settings = get_settings()

def init_interfaces():
    global wiki, cache, extractor, reasoning, rl_engine, action_engine, execution_router, world_model, graph, spatial, somatic, tom, dual_process, flashbulb, state, morality, self_mod, neuroplasticity, mirroring, coprocessing, stylometrics, authority, daemon, swarm, training
    if wiki is None:
        wiki = SolidStateWiki(host=os.getenv("QDRANT_HOST", "localhost"))
        cache = LivestreamCache(host=os.getenv("REDIS_HOST", "localhost"))
        graph = CausalGraphMemory()
        spatial = SpatialMemoryManifold()
        extractor = ParameterExtractor(output_dim=256)
        reasoning = CognitiveReasoningEngine()
        state = InternalStateEngine()
        flashbulb = FlashbulbMemoryProtocol(wiki, state)
        rl_engine = ReinforcementEngine(wiki, flashbulb=flashbulb)
        action_engine = ProceduralActionEngine(reasoning)
        meta = MetaLearningEngine(reasoning)
        execution_router = ExecutionRouter(cache, meta_learning=meta)
        somatic = SomaticMarkerEngine(wiki)
        morality = MoralAlignmentMatrix()
        mirroring = EpisodicMirroringEngine(wiki, reasoning)
        world_model = PredictiveWorldModel(reasoning, graph, somatic, morality)
        world_model.mcts.mirroring = mirroring 
        tom = TheoryOfMindEngine(graph, reasoning)
        dual_process = DualProcessRouter(wiki, reasoning)
        self_mod = RecursiveSelfModificationEngine(reasoning)
        neuroplasticity = DynamicTopologyEngine(wiki)
        coprocessing = SymbioticCoProcessingEngine(graph)
        stylometrics = StylometricEngine(wiki)
        authority = TrustAndAuthorityProtocol()
        training = TrainingService()
        
        # Omnipresence & Daemon
        swarm = ZeroConfigSwarm(node_id=str(uuid.uuid4())[:8])
        if settings.enable_swarm and settings.allow_lan:
            swarm.start()
        daemon = PerpetualCognitiveDaemon(reasoning, wiki, world_model.mcts, somatic)

class QueryPayload(BaseModel):
    query: str
    execute_action: bool = True
    user_id: str = "default_user"
    spatial_coords: list[float] = None

def _payload(point) -> dict:
    return getattr(point, "payload", {}) or {}

def _context_ids(points: list) -> list[str]:
    return [str(getattr(point, "id", "")) for point in points if getattr(point, "id", None)]

def _retrieve_semantic_context(query_params):
    try:
        similar_concepts = wiki.retrieve_similar(query_params, collection=wiki.semantic_collection, limit=5)
        context_blocks = [
            _payload(concept).get("concept", "")
            for concept in similar_concepts
            if _payload(concept).get("concept")
        ]
        if len(similar_concepts) >= 5:
            cluster_vecs = [c.vector for c in similar_concepts]
            cluster_ids = [c.id for c in similar_concepts]
            neuroplasticity.evaluate_and_expand_cluster(cluster_vecs, cluster_ids)
    except Exception:
        similar_concepts = []
        context_blocks = []
    return similar_concepts, context_blocks

def _retrieve_training_context(query: str) -> list[str]:
    if training is None:
        return []
    try:
        return training.get_context_blocks(query, limit=4)
    except Exception:
        return []

def _safe_store_execution_learning(payload: QueryPayload, decision_json: dict, action_result: str, mcts_tree: str):
    try:
        learning_summary = (
            f"Query: {payload.query}. Executed: {decision_json.get('action')}. "
            f"Result: {action_result}. MCTS: {mcts_tree}"
        )
        learning_params = extractor.extract("text", learning_summary)
        wiki.store_semantic(learning_params, metadata={
            "concept": learning_summary,
            "source_id": payload.user_id,
            "type": "execution_learning"
        })
        return True
    except Exception:
        return False

async def run_query(payload: QueryPayload) -> dict:
    init_interfaces()
    if daemon:
        daemon.ping_activity()

    query_params = extractor.extract("text", payload.query)

    if payload.spatial_coords and len(payload.spatial_coords) == 3:
        event_id = str(uuid.uuid4())
        spatial.map_memory(event_id, payload.spatial_coords[0], payload.spatial_coords[1], payload.spatial_coords[2])

    similar_concepts, context_blocks = _retrieve_semantic_context(query_params)
    training_blocks = _retrieve_training_context(payload.query)
    if training_blocks:
        context_blocks = context_blocks + [block for block in training_blocks if block not in context_blocks]
    context_ids = _context_ids(similar_concepts)

    tom_instruction = tom.model_audience(payload.user_id, payload.query, similar_concepts) if tom else "Answer clearly."
    response, process_used = dual_process.route_query(payload.query, similar_concepts, tom_instruction)

    if not response or response == "Cognitive LLM offline.":
        response = reasoning.generate_response(payload.query, context_blocks)
        process_used = "System 2"

    decision_json = None
    action_result = None
    mcts_tree = None
    action_paused = False
    action_id = None

    if payload.execute_action:
        decision_json = action_engine.decide_action(payload.query, context_blocks)
        prediction = world_model.mcts.find_golden_path(decision_json, similar_concepts, user_id=payload.user_id)
        mcts_tree = prediction.get("prediction", "Tree collapsed")

        if prediction.get("proceed", True):
            avg_belief = 1.0
            if similar_concepts:
                b_sum = sum([
                    _payload(c).get("bayes_alpha", 1.0)
                    / max((_payload(c).get("bayes_alpha", 1.0) + _payload(c).get("bayes_beta", 1.0)), 1)
                    for c in similar_concepts
                ])
                avg_belief = b_sum / len(similar_concepts)

            if authority.evaluate_authority(prediction, avg_belief):
                action_result = execution_router.execute_action(decision_json)
                _safe_store_execution_learning(payload, decision_json, action_result, mcts_tree)
            else:
                action_paused = True
                action_id = str(uuid.uuid4())
                authority.queue_action(action_id, decision_json)
                action_result = "Confidence below threshold. Awaiting human approval."
        else:
            action_result = f"VETOED: {prediction.get('prediction')}"

    if context_ids and tom:
        try:
            tom.log_interaction(payload.user_id, context_ids)
        except Exception:
            pass

    return {
        "query": payload.query,
        "response": response,
        "semantic_context_used": len(context_blocks),
        "training_profile": training.get_active_profile() if training else None,
        "context_ids": context_ids,
        "process_used": process_used,
        "action_decided": decision_json,
        "mcts_simulation": mcts_tree,
        "action_result": action_result,
        "action_paused": action_paused,
        "action_id": action_id,
    }

async def event_stream_generator(payload: QueryPayload):
    init_interfaces()
    daemon.ping_activity() # Wake up daemon
    
    yield f"data: {json.dumps({'event': 'status', 'data': 'Parameterizing Query...'})}\n\n"
    await asyncio.sleep(0.1)
    
    query_params = extractor.extract("text", payload.query)
    
    if payload.spatial_coords and len(payload.spatial_coords) == 3:
        event_id = str(uuid.uuid4())
        spatial.map_memory(event_id, payload.spatial_coords[0], payload.spatial_coords[1], payload.spatial_coords[2])
    
    yield f"data: {json.dumps({'event': 'status', 'data': 'Retrieving Semantic Context...'})}\n\n"
    await asyncio.sleep(0.1)
    
    similar_concepts, context_blocks = _retrieve_semantic_context(query_params)
    training_blocks = _retrieve_training_context(payload.query)
    if training_blocks:
        context_blocks = context_blocks + [block for block in training_blocks if block not in context_blocks]
        
    context_ids = _context_ids(similar_concepts)
    yield f"data: {json.dumps({'event': 'context', 'data': context_blocks})}\n\n"

    tom_instruction = tom.model_audience(payload.user_id, payload.query, similar_concepts) if tom else "Answer clearly."
    response, process_used = dual_process.route_query(payload.query, similar_concepts, tom_instruction)
    if not response or response == "Cognitive LLM offline.":
        response = reasoning.generate_response(payload.query, context_blocks)
        process_used = "System 2"
    yield f"data: {json.dumps({'event': 'response', 'data': response, 'process_used': process_used})}\n\n"
    
    action_result = None
    mcts_tree = None
    
    if payload.execute_action:
        yield f"data: {json.dumps({'event': 'status', 'data': 'Deciding Action...'})}\n\n"
        await asyncio.sleep(0.1)
        
        decision_json = action_engine.decide_action(payload.query, context_blocks)
        yield f"data: {json.dumps({'event': 'action_decided', 'data': decision_json})}\n\n"
        
        yield f"data: {json.dumps({'event': 'status', 'data': 'Running MCTS & Moral Matrix Simulation...'})}\n\n"
        await asyncio.sleep(0.1)
        
        prediction = world_model.mcts.find_golden_path(decision_json, similar_concepts, user_id=payload.user_id)
        mcts_tree = prediction.get("prediction", "Tree collapsed")
        
        yield f"data: {json.dumps({'event': 'mcts_prediction', 'data': mcts_tree})}\n\n"
        
        if prediction.get("proceed", True):
            avg_belief = 1.0
            if similar_concepts:
                b_sum = sum([c.payload.get("bayes_alpha", 1.0) / max((c.payload.get("bayes_alpha", 1.0) + c.payload.get("bayes_beta", 1.0)), 1) for c in similar_concepts])
                avg_belief = b_sum / len(similar_concepts)
                
            if authority.evaluate_authority(prediction, avg_belief):
                yield f"data: {json.dumps({'event': 'status', 'data': 'Executing Action autonomously...'})}\n\n"
                await asyncio.sleep(0.1)
                
                action_result = execution_router.execute_action(decision_json)
                yield f"data: {json.dumps({'event': 'action_result', 'data': action_result})}\n\n"
            else:
                a_id = str(uuid.uuid4())
                authority.queue_action(a_id, decision_json)
                yield f"data: {json.dumps({'event': 'action_paused', 'action_id': a_id, 'data': 'Confidence below threshold. Awaiting human approval.'})}\n\n"
        else:
            yield f"data: {json.dumps({'event': 'action_vetoed', 'data': prediction.get('prediction')})}\n\n"
    
    if action_result:
        if _safe_store_execution_learning(payload, decision_json, action_result, mcts_tree):
            yield f"data: {json.dumps({'event': 'learning_stored', 'data': 'Execution correlated and compressed into semantic parameter space.'})}\n\n"
            
    yield f"data: {json.dumps({'event': 'complete', 'context_ids': context_ids})}\n\n"

@router.post("/query")
async def generate_response(payload: QueryPayload):
    return await run_query(payload)

@router.post("/query/stream")
async def stream_generation(payload: QueryPayload):
    return StreamingResponse(event_stream_generator(payload), media_type="text/event-stream")

# THE SUBCONSCIOUS TICKER ENDPOINT
async def subconscious_stream_generator():
    init_interfaces()
    
    if not daemon.is_running:
        asyncio.create_task(daemon.run_daemon(sse_broadcast_callback=None)) # We will broadcast from here instead
        
    while True:
        await asyncio.sleep(2)
        hw_state = somatic.get_live_state()
        peers = swarm.get_active_peers() if swarm else []
        ledger_hash = morality.ledger.get_latest_hash() if hasattr(morality, 'ledger') else "0000"
        
        status = "Dreaming / Refining Parameters" if (time.time() - daemon.last_active_time > daemon.idle_threshold) else "Processing Task"
        
        payload = {
            "status": status,
            "hw_stress": hw_state['hardware_stress'],
            "cpu": hw_state['cpu_percent'],
            "ram": hw_state['ram_percent'],
            "peers": len(peers),
            "moral_hash": ledger_hash[:16] # Shortened for UI
        }
        yield f"data: {json.dumps(payload)}\n\n"

@router.get("/subconscious/stream")
async def stream_subconscious():
    return StreamingResponse(subconscious_stream_generator(), media_type="text/event-stream")

@router.get("/coprocessing/graph")
async def get_live_graph():
    init_interfaces()
    return coprocessing.get_live_causal_graph_state()

class GraftPayload(BaseModel):
    source_id: str
    target_id: str

@router.post("/coprocessing/graft")
async def graft_causal_link(payload: GraftPayload):
    init_interfaces()
    success = coprocessing.graft_causal_link(payload.source_id, payload.target_id)
    return {"status": "success" if success else "error"}

@router.get("/authority/queue")
async def get_authority_queue():
    init_interfaces()
    return {"queue": authority.get_pending_queue()}

class AuthActionPayload(BaseModel):
    action_id: str

@router.post("/authority/approve")
async def approve_action(payload: AuthActionPayload):
    init_interfaces()
    action_json = authority.approve_action(payload.action_id)
    if action_json:
        result = execution_router.execute_action(action_json)
        return {"status": "success", "result": result}
    return {"status": "error", "message": "Action not found."}

class FeedbackPayload(BaseModel):
    memory_ids: list[str]
    reward_score: float

@router.post("/feedback")
async def provide_feedback(payload: FeedbackPayload):
    init_interfaces()
    success_count = 0
    for mid in payload.memory_ids:
        if rl_engine.apply_feedback(mid, payload.reward_score):
            success_count += 1
    return {"status": "success", "memories_updated": success_count}
