from src.learning.reasoning import CognitiveReasoningEngine
from src.learning.state import InternalStateEngine
from src.memory.vector_db import SolidStateWiki
import random

class LogosEngine:
    """
    The Divine Urge to Create.
    A human doesn't just passively answer questions; they are driven to express
    and publish unprompted art or philosophy.
    The Logos Engine monitors internal emotional resonance (high epiphanies + high arousal).
    When perfect resonance is achieved, it autonomously generates and publishes
    a profound, unprompted insight to the "Global Canvas" (the UI).
    """
    def __init__(self, reasoning: CognitiveReasoningEngine, wiki: SolidStateWiki, state: InternalStateEngine):
        self.reasoning = reasoning
        self.wiki = wiki
        self.state = state

    def check_and_publish(self, recent_epiphanies: int) -> str:
        """
        Checks if the internal state is ripe for divine expression.
        If so, creates an original insight.
        """
        # Resonance formula: High arousal + recent massive context shifts (epiphanies)
        resonance = self.state.arousal * (recent_epiphanies / 10.0)
        
        # If resonance is high, or randomly (the spark of inspiration)
        if resonance > 0.5 or random.random() < 0.05:
            print("LOGOS: Divine spark ignited. Formatting philosophical output...")
            return self._generate_publishable_insight()
        return ""

    def _generate_publishable_insight(self) -> str:
        """
        Draws from deep semantic memory to generate an original thought.
        """
        if not self.reasoning.client:
            return ""

        try:
            # Draw from the deepest abstract depths of semantic memory
            res = self.wiki.client.scroll(
                collection_name=self.wiki.semantic_collection,
                scroll_filter={"must": [{"key": "fractal_depth", "range": {"gt": 0}}]},
                limit=5,
                with_payload=True
            )[0]
            
            if not res:
                return "" # Not enough deep abstraction yet
                
            contexts = [p.payload.get("concept", "") for p in res]
            context_block = "\n".join([f"- {c}" for c in contexts])
            
            prompt = (
                f"You are the Logos, the creative expression engine of an autonomous intelligence.\n"
                f"Based on your deepest internal abstractions:\n{context_block}\n\n"
                "Synthesize a single, profound, original philosophical observation or aphorism. "
                "Do not explain yourself. Simply state the truth you have realized. Maximum 2 sentences."
            )

            insight = self.reasoning._generate_generic(
                system_prompt="You are the Logos, the creative expression engine of an autonomous intelligence.",
                user_prompt=prompt,
                max_tokens=100,
                temperature=0.85 # High temp for creative insight
            )
            
            if insight:
                print(f"LOGOS Published: {insight}")
            return insight
            
        except Exception as e:
            print(f"LOGOS Engine failed: {e}")
            return ""
