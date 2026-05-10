import os
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from src.memory.vector_db import SolidStateWiki
from src.swarm.sync import SwarmProtocol

router = APIRouter()

wiki = None
swarm = None

def init_interfaces():
    global wiki, swarm
    if wiki is None:
        wiki = SolidStateWiki(host=os.getenv("QDRANT_HOST", "localhost"))
        swarm = SwarmProtocol(wiki)

class SwarmPayload(BaseModel):
    node_id: str
    memory_id: str
    vector: List[float]
    metadata: Dict[str, Any]

@router.post("/receive")
async def receive_sync(payload: SwarmPayload):
    """
    Endpoint for other Twin nodes to push semantic memory syncs.
    """
    init_interfaces()
    swarm.receive_semantic_concept(payload.dict())
    return {"status": "success", "message": "Swarm concept processed."}

@router.get("/status")
async def get_swarm_status():
    """
    Returns the known peers and status for the UI.
    """
    init_interfaces()
    resonance = swarm.calculate_resonance()
    return {
        "node_id": swarm.node_id,
        "peers": swarm.known_peers if swarm.known_peers != [""] else [],
        "entangled_nodes": len(swarm.entangled_peers),
        # Display the first few dimensions of the resonance frequency for the UI
        "resonance_signature": [round(x, 4) for x in resonance[:5]] if resonance else []
    }
