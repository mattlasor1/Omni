import json
from src.learning.reasoning import CognitiveReasoningEngine

class ProceduralActionEngine:
    """
    Translates semantic knowledge into procedural action.
    While the generation API creates text responses, this engine allows the
    digital twin to formulate structured plans or tool invocations based on 
    what it has learned.
    """
    def __init__(self, reasoning_engine: CognitiveReasoningEngine):
        self.reasoning = reasoning_engine

    def decide_action(self, situation_context: str, semantic_memories: list[str]) -> dict:
        """
        Given a situation and relevant semantic memories, decides on a structured
        action to take (e.g., API call, script execution, or alert).
        """
        if not self.reasoning.client:
            return {"action": "none", "reason": "Cognitive LLM offline"}

        memory_block = "\n".join([f"- {m}" for m in semantic_memories])
        
        prompt = (
            f"Situation: {situation_context}\n\n"
            f"Relevant Knowledge:\n{memory_block}\n\n"
            "Based ONLY on your knowledge, decide on the best action to take. "
            "Output your decision strictly as a JSON object with two keys: 'action' (the command or tool) "
            "and 'reason' (why you chose this based on memory)."
        )

        try:
            action_str = self.reasoning._generate_generic(
                system_prompt="You are a procedural execution engine. You map knowledge to JSON actions. Respond ONLY with raw JSON.",
                user_prompt=prompt,
                max_tokens=150,
                temperature=0.2
            )
            
            # Try to extract json if it hallucinates markdown
            if "{" in action_str and "}" in action_str:
                action_str = "{" + action_str.split("{", 1)[1].rsplit("}", 1)[0] + "}"
                
            action_json = json.loads(action_str)
            return action_json
        except Exception as e:
            print(f"Action generation failed: {e}")
            return {"action": "error", "reason": str(e)}
