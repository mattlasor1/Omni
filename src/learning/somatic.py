from src.memory.vector_db import SolidStateWiki

class SomaticMarkerEngine:
    """
    Implements the Somatic Marker Hypothesis (Damasio).
    Humans don't evaluate every decision logically; we rely on "gut feelings" 
    associated with past experiences to instantly veto or approve actions.
    This engine associates a visceral 'valence' (-1.0 to 1.0) with concepts.
    """
    def __init__(self, wiki: SolidStateWiki):
        self.wiki = wiki

    def apply_somatic_marker(self, memory_id: str, intensity: float):
        """
        Binds a visceral feeling to a memory. 
        Negative intensity = Pain/Aversion. Positive = Pleasure/Attraction.
        """
        try:
            points = self.wiki.client.retrieve(
                collection_name=self.wiki.semantic_collection,
                ids=[memory_id]
            )
            if not points: return
            
            point = points[0]
            current_valence = point.payload.get("somatic_valence", 0.0)
            
            # Update visceral feeling
            new_valence = max(-1.0, min(1.0, current_valence + (intensity * 0.5)))
            
            point.payload["somatic_valence"] = new_valence
            
            self.wiki.client.set_payload(
                collection_name=self.wiki.semantic_collection,
                payload=point.payload,
                points=[point.id]
            )
            print(f"SOMATIC: Bound feeling of {new_valence:.2f} to memory {memory_id}")
        except Exception as e:
            print(f"Somatic binding failed: {e}")

    def evaluate_gut_feeling(self, context_memories: list) -> float:
        """
        Takes a list of retrieved Qdrant points (memories) relevant to a situation
        and returns the aggregate "gut feeling".
        If it returns a deeply negative score, the action can be vetoed instantly
        without needing logical LLM simulation.
        """
        if not context_memories: return 0.0
        
        total_valence = 0.0
        count = 0
        for memory in context_memories:
            # Check if this is a raw point struct or dictionary
            payload = memory.payload if hasattr(memory, 'payload') else memory.get('payload', {})
            valence = payload.get("somatic_valence", 0.0)
            if valence != 0.0:
                total_valence += valence
                count += 1
                
        if count == 0: return 0.0
        return total_valence / count
