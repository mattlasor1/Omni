from typing import List, Dict, Any
from src.learning.reasoning import CognitiveReasoningEngine

class CuriosityEngine:
    """
    Humans don't just passively absorb data; they actively seek it when confused.
    This engine identifies gaps in knowledge (clusters of memories with high
    variance or contradictory signals) and formulates proactive questions to ask.
    """
    def __init__(self, reasoning_engine: CognitiveReasoningEngine):
        self.reasoning = reasoning_engine

    def evaluate_cluster_for_curiosity(self, cluster_payloads: List[Dict[str, Any]]) -> str:
        """
        Takes a cluster of episodic memories. If they are diverse, unclear, 
        or seemingly contradictory, it generates a question to resolve the ambiguity.
        """
        # Heuristic: If cluster size is very small, we might lack data on this topic.
        if len(cluster_payloads) < 2:
            return "" # Not enough data to even formulate a hypothesis
            
        if not self.reasoning.client:
            return "I have detected some anomalous data but lack the cognitive API to formulate a specific question about it."

        contexts = [m.get("content", str(m)) for m in cluster_payloads if "content" in m]
        
        prompt = (
            "You are the curiosity module of an advanced digital twin. "
            "Look at the following related observations. What is missing? What is confusing? "
            "Formulate ONE concise, direct question that, if answered, would clarify this topic or fill the knowledge gap.\n\n"
        )
        for i, c in enumerate(contexts[:5]): # Limit context size
            prompt += f"{i+1}. {c}\n"
            
        try:
            question = self.reasoning._generate_generic(
                system_prompt="You are a proactive curiosity engine. Ask one clarifying question based on incomplete observations.",
                user_prompt=prompt,
                max_tokens=100,
                temperature=0.8 # Higher temp for more creative/exploratory questions
            )
            return question
        except Exception as e:
            print(f"Curiosity formulation failed: {e}")
            return ""
