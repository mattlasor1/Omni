import os
import uuid
import json
import asyncio
import time
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.memory.solid_state import SolidStateWiki
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

def init_interfaces():
    global wiki, cache, extractor, reasoning, rl_engine, action_engine, execution_router, world_model, graph, spatial, somatic, tom, dual_process, flashbulb, state, morality, self_mod, neuroplasticity, mirroring, coprocessing, stylometrics, authority, daemon, swarm
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
        
        # Omnipresence & Daemon
        swarm = ZeroConfigSwarm(node_id=str(uuid.uuid4())[:8])
        swarm.start()
        daemon = PerpetualCognitiveDaemon(reasoning, wiki, world_model.mcts, somatic)

class QueryPayload(BaseModel):
    query: str
    execute_action: bool = True
    user_id: str = "default_user"
    spatial_coords: list[float] = None

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
    
    try:
        similar_concepts = wiki.retrieve_similar(query_params, collection=wiki.semantic_collection, limit=5)
        context_blocks = [c.payload.get("concept", "") for c in similar_concepts if "concept" in c.payload]
        if len(similar_concepts) >= 5:
            cluster_vecs = [c.vector for c in similar_concepts]
            cluster_ids = [c.id for c in similar_concepts]
            neuroplasticity.evaluate_and_expand_cluster(cluster_vecs, cluster_ids)
    except Exception as e:
        context_blocks = []
        similar_concepts = []
        
    context_ids = [c.id for c in similar_concepts]
    yield f"data: {json.dumps({'event': 'context', 'data': context_blocks})}\n\n"
    
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
        try:
            learning_summary = f"Query: {payload.query}. Executed: {decision_json.get('action')}. Result: {action_result}. MCTS: {mcts_tree}"
            learning_params = extractor.extract("text", learning_summary)
            wiki.store_semantic(learning_summary, learning_params, payload.user_id)
            yield f"data: {json.dumps({'event': 'learning_stored', 'data': 'Execution correlated and compressed into semantic parameter space.'})}\n\n"
        except Exception as e:
            pass
            
    yield f"data: {json.dumps({'event': 'complete', 'context_ids': context_ids})}\n\n"

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
