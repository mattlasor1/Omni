import numpy as np
from src.memory.vector_db import SolidStateWiki
from src.learning.flashbulb import FlashbulbMemoryProtocol

class ReinforcementEngine:
    """
    Implements a human-like feedback loop.
    When the twin applies knowledge (generates an output/action) and receives
    feedback (positive/negative), this engine updates the semantic memory weights.
    Negative feedback reduces confidence/preservation, causing the memory to be
    more easily overwritten or forgotten in future regressions.
    """
    def __init__(self, wiki_interface: SolidStateWiki, flashbulb: FlashbulbMemoryProtocol = None):
        self.wiki = wiki_interface
        self.learning_rate = 0.1
        self.flashbulb = flashbulb

    def apply_feedback(self, memory_id: str, reward_score: float):
        """
        Adjusts the metadata (confidence/preservation weights) of a semantic memory
        based on a reward signal [-1.0 (bad) to 1.0 (good)].
        """
        try:
            # 1. Retrieve the specific memory point
            points = self.wiki.client.retrieve(
                collection_name=self.wiki.semantic_collection,
                ids=[memory_id]
            )
            
            if not points:
                print(f"RL Error: Memory {memory_id} not found.")
                return False
                
            point = points[0]
            current_payload = point.payload or {}
            
            # Current confidence (default 1.0)
            current_confidence = current_payload.get("rl_confidence", 1.0)
            
            # 2. Apply Reward (Simple Q-learning style update on confidence)
            # If reward is negative, confidence drops. If positive, it reinforces.
            new_confidence = current_confidence + (self.learning_rate * reward_score)
            
            # Bound between 0.1 (almost forgotten) and 2.0 (highly reinforced truth)
            new_confidence = max(0.1, min(2.0, new_confidence))
            
            # Update Payload
            current_payload["rl_confidence"] = new_confidence
            
            # 3. Save back to Vector DB
            self.wiki.client.set_payload(
                collection_name=self.wiki.semantic_collection,
                payload=current_payload,
                points=[memory_id]
            )
            
            # 4. Check for Flashbulb forging (Trauma/Ecstasy)
            if self.flashbulb:
                self.flashbulb.check_and_forge(memory_id, reward_score)
            
            print(f"RL Feedback applied. Memory {memory_id} confidence is now {new_confidence:.2f}")
            return True
            
        except Exception as e:
            print(f"RL Feedback Failed: {e}")
            return False
