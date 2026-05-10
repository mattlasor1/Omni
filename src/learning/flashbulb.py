from src.memory.vector_db import SolidStateWiki
from src.learning.state import InternalStateEngine

class FlashbulbMemoryProtocol:
    """
    Implements Flashbulb Memories (Trauma & Ecstasy).
    When the twin experiences extreme RL feedback paired with peak arousal,
    the memory bypasses normal Bayesian updating and Synaptic Pruning.
    It becomes an immutable 'Core Drive' or 'Trauma', heavily biasing
    future somatic evaluations and causal pathfinding.
    """
    def __init__(self, wiki: SolidStateWiki, state: InternalStateEngine):
        self.wiki = wiki
        self.state = state

    def check_and_forge(self, memory_id: str, reward_score: float):
        """
        Evaluates an RL feedback event to see if it qualifies for Flashbulb forging.
        Requires high absolute reward (|score| > 0.8) AND high arousal (> 0.8).
        """
        if abs(reward_score) < 0.8 or self.state.arousal < 0.8:
            return False
            
        try:
            points = self.wiki.client.retrieve(
                collection_name=self.wiki.semantic_collection,
                ids=[memory_id]
            )
            if not points: return False
            
            point = points[0]
            
            # Check if it's already a flashbulb memory
            if point.payload.get("flashbulb", False):
                return False
                
            # Forge the memory
            memory_type = "ECSTASY" if reward_score > 0 else "TRAUMA"
            print(f"FLASHBULB FORGED: Intense emotional event triggered a {memory_type} core memory ({memory_id}).")
            
            point.payload["flashbulb"] = True
            point.payload["flashbulb_type"] = memory_type
            
            # Lock Bayesian confidence to near infinity so it cannot be unlearned easily
            point.payload["bayes_alpha"] += 1000.0 if memory_type == "ECSTASY" else 0.0
            point.payload["bayes_beta"] += 1000.0 if memory_type == "TRAUMA" else 0.0
            
            # Max out somatic valence
            point.payload["somatic_valence"] = 1.0 if memory_type == "ECSTASY" else -1.0
            
            self.wiki.client.set_payload(
                collection_name=self.wiki.semantic_collection,
                payload=point.payload,
                points=[point.id]
            )
            
            return True
            
        except Exception as e:
            print(f"Flashbulb forging failed: {e}")
            return False
