import os
from fastapi import APIRouter
from pydantic import BaseModel
from src.memory.vector_db import SolidStateWiki
from src.learning.engine import ParameterExtractor
from src.learning.reasoning import CognitiveReasoningEngine
from src.learning.reinforcement import ReinforcementEngine
from src.generation.action import ProceduralActionEngine
from src.execution.tools import ExecutionRouter
from src.memory.cache import LivestreamCache
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

def init_interfaces():
    global wiki, cache, extractor, reasoning, rl_engine, action_engine, execution_router
    if wiki is None:
        wiki = SolidStateWiki(host=os.getenv("QDRANT_HOST", "localhost"))
        cache = LivestreamCache(host=os.getenv("REDIS_HOST", "localhost"))
        extractor = ParameterExtractor(output_dim=256)
        reasoning = CognitiveReasoningEngine()
        rl_engine = ReinforcementEngine(wiki)
        action_engine = ProceduralActionEngine(reasoning)
        execution_router = ExecutionRouter(cache)

class QueryPayload(BaseModel):
    query: str
    execute_action: bool = False

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
    
    # 2. Retrieve relevant context from semantic memory
    try:
        similar_concepts = wiki.retrieve_similar(query_params, collection=wiki.semantic_collection, limit=3)
        context_blocks = [c.payload.get("concept", "") for c in similar_concepts if "concept" in c.payload]
    except Exception as e:
        print(f"Memory retrieval error: {e}")
        context_blocks = []
        
    # Extract IDs for RL feedback binding
    context_ids = [c.id for c in similar_concepts]
    
    # 3. Generate response using LLM Reasoning Engine
    response = reasoning.generate_response(payload.query, context_blocks)
    
    action_result = None
    if payload.execute_action:
        # 4. If autonomous execution is enabled, decide and act
        decision_json = action_engine.decide_action(payload.query, context_blocks)
        action_result = execution_router.execute_action(decision_json)
        response += f"\n\n[Action Taken]: {decision_json.get('action')} - {action_result}"
    
    return {
        "query": payload.query,
        "response": response,
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
