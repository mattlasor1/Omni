import os
from fastapi import APIRouter
from pydantic import BaseModel
from src.memory.vector_db import SolidStateWiki
from src.learning.engine import ParameterExtractor
from src.learning.reasoning import CognitiveReasoningEngine
from src.learning.reinforcement import ReinforcementEngine

router = APIRouter()

# Defer initialization
wiki = None
extractor = None
reasoning = None
rl_engine = None

def init_interfaces():
    global wiki, extractor, reasoning, rl_engine
    if wiki is None:
        wiki = SolidStateWiki(host=os.getenv("QDRANT_HOST", "localhost"))
        extractor = ParameterExtractor(output_dim=256)
        reasoning = CognitiveReasoningEngine()
        rl_engine = ReinforcementEngine(wiki)

class QueryPayload(BaseModel):
    query: str

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
    
    return {
        "query": payload.query,
        "response": response,
        "semantic_context_used": len(context_blocks),
        "context_ids": context_ids # Returned so UI can send feedback to these memories
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
