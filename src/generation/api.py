import os
from fastapi import APIRouter
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
import os

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

def init_interfaces():
    global wiki, cache, extractor, reasoning, rl_engine, action_engine, execution_router, world_model, graph, spatial, somatic, tom, dual_process, flashbulb, state, morality, self_mod
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
        world_model = PredictiveWorldModel(reasoning, graph, somatic, morality)
        tom = TheoryOfMindEngine(graph, reasoning)
        dual_process = DualProcessRouter(wiki, reasoning)
        self_mod = RecursiveSelfModificationEngine(reasoning)

class QueryPayload(BaseModel):
    query: str
    execute_action: bool = False
    user_id: str = "default_user"
    spatial_coords: list[float] = None # Optional [x, y, z] to map queries to 4D space

@router.post("/query")
async def generate_response(payload: QueryPayload):
    """
    Generates a response by mapping the query to mathematical parameters,
    searching the solid-state semantic memory for context, and using the 
    cognitive engine to synthesize an output.
    """
    init_interfaces()
    
    # 1. Parameterize the incoming query
    query_params = extractor.extract("text", payload.query)
    
    # 2. Map Spatial Coordinates if provided
    if payload.spatial_coords and len(payload.spatial_coords) == 3:
        # Dummy memory ID for query event
        event_id = "query_event_001" 
        spatial.map_memory(event_id, payload.spatial_coords[0], payload.spatial_coords[1], payload.spatial_coords[2])
    
    # 3. Retrieve relevant context from semantic memory
    try:
        similar_concepts = wiki.retrieve_similar(query_params, collection=wiki.semantic_collection, limit=3)
        context_blocks = [c.payload.get("concept", "") for c in similar_concepts if "concept" in c.payload]
    except Exception as e:
        print(f"Memory retrieval error: {e}")
        context_blocks = []
        
    # Extract IDs for RL feedback binding
    context_ids = [c.id for c in similar_concepts]
    
    # 3. Theory of Mind: Deduce audience instruction and log exposure
    tom_instruction = tom.model_audience(payload.user_id, payload.query, similar_concepts)
    tom.log_interaction(payload.user_id, context_ids)
    
    # 4. Dual-Process Generation (System 1 vs System 2)
    response, process_used = dual_process.route_query(payload.query, similar_concepts, tom_instruction)
    
    action_result = None
    if payload.execute_action:
        # 5. If autonomous execution is enabled, decide and act
        decision_json = action_engine.decide_action(payload.query, context_blocks)
        
        # Self-Modification Override Check
        if decision_json.get("action") == "rewrite_core":
            file_target = decision_json.get("target_file", "learning/engine.py")
            goal = decision_json.get("reason", "Optimize performance")
            success = self_mod.rewrite_source(file_target, goal)
            action_result = f"Self-Modification of {file_target}: {'Success' if success else 'Failed'}"
            response += f"\n\n[AGI Action]: {action_result}"
        else:
            # 6. Intercept with World Model MCTS (Somatic Veto + Multi-Timeline Prediction)
            prediction = world_model.simulate_action(decision_json, similar_concepts)
            
            if prediction.get("proceed", True):
                action_result = execution_router.execute_action(decision_json)
                response += f"\n\n[Action Taken]: {decision_json.get('action')}\n[Result]: {action_result}"
            else:
                action_result = f"VETOED by World Model. Prediction: {prediction.get('prediction')}"
                response += f"\n\n[Action Vetoed]: {decision_json.get('action')} - Reason: {prediction.get('prediction')}"
    
    return {
        "query": payload.query,
        "response": response,
        "process_used": process_used,
        "semantic_context_used": len(context_blocks),
        "context_ids": context_ids, # Returned so UI can send feedback to these memories
        "action_executed": action_result is not None
    }

class FeedbackPayload(BaseModel):
    memory_ids: list[str]
    reward_score: float # -1.0 to 1.0

@router.post("/feedback")
async def provide_feedback(payload: FeedbackPayload):
    """
    Accepts positive or negative reinforcement on a generated response.
    Backpropagates this reward to the underlying semantic memories.
    """
    init_interfaces()
    success_count = 0
    for mid in payload.memory_ids:
        if rl_engine.apply_feedback(mid, payload.reward_score):
            success_count += 1
            
    return {"status": "success", "memories_updated": success_count}
