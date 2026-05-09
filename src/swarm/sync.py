import os
import requests
from typing import List, Dict, Any
from src.memory.vector_db import SolidStateWiki

class SwarmProtocol:
    """
    Manages the P2P Swarm Synchronization for Distributed OmniTwins.
    Allows multiple nodes (e.g., Vision Node, Audio Node, Core Node) to share
    their compressed mathematical semantic memory over the network.
    """
    def __init__(self, wiki_interface: SolidStateWiki):
        self.wiki = wiki_interface
        # In a real swarm, this would be a dynamic list via Consul or etcd.
        self.known_peers = os.getenv("SWARM_PEERS", "").split(",")
        self.node_id = os.getenv("NODE_ID", "primary_core_node")

    def broadcast_new_semantic_concept(self, memory_id: str, vector: list, metadata: dict):
        """
        When this node dreams/reflects and creates a new semantic concept,
        it broadcasts the math to its peers.
        """
        if not self.known_peers or self.known_peers == [""]:
            return
            
        payload = {
            "node_id": self.node_id,
            "memory_id": memory_id,
            "vector": vector,
            "metadata": metadata
        }
        
        for peer_url in self.known_peers:
            try:
                if peer_url:
                    requests.post(f"{peer_url}/api/v1/swarm/receive", json=payload, timeout=2.0)
                    print(f"Broadcasted concept to peer: {peer_url}")
            except Exception as e:
                print(f"Swarm Broadcast to {peer_url} failed: {e}")

    def receive_semantic_concept(self, payload: Dict[str, Any]):
        """
        Receives a compressed semantic concept from another node.
        """
        sender_node = payload.get("node_id")
        vector = payload.get("vector")
        metadata = payload.get("metadata", {})
        
        metadata["source_node"] = sender_node
        
        # Check if we already have it or something similar
        import numpy as np
        query_vector = np.array(vector)
        
        similar = self.wiki.retrieve_similar(query_vector, collection=self.wiki.semantic_collection, limit=1)
        
        # If the other node's math is highly novel to us, store it.
        # Otherwise, our existing knowledge covers it.
        if similar and similar[0].score > 0.95:
            print(f"Ignored Swarm Sync from {sender_node}: Concept already known.")
        else:
            self.wiki.store_semantic(query_vector, metadata=metadata)
            print(f"Absorbed novel Swarm Sync from {sender_node}: {metadata.get('concept', 'Unknown Concept')}")
