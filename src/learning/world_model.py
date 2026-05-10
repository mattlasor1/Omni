from typing import Dict, Any
from src.learning.reasoning import CognitiveReasoningEngine
from src.memory.graph_db import CausalGraphMemory
from src.learning.somatic import SomaticMarkerEngine

class PredictiveWorldModel:
    """
    The 'Mind's Eye' or Imagination of the Digital Twin.
    Before taking an action, this engine evaluates the "gut feeling" via somatic markers.
    If the gut feeling is neutral or positive, it simulates the action logically 
    using the LLM to predict the outcome.
    """
    def __init__(self, reasoning: CognitiveReasoningEngine, causal_graph: CausalGraphMemory, somatic: SomaticMarkerEngine):
        self.reasoning = reasoning
        self.graph = causal_graph
        self.somatic = somatic

    def simulate_action(self, action_json: Dict[str, Any], current_context_points: list) -> Dict[str, Any]:
        """
        Simulates an action and returns a prediction and a go/no-go decision.
        Expects a list of Qdrant point objects to evaluate somatic markers.
        """
        # 1. System 1 Somatic Check (Gut Feeling)
        gut_feeling = self.somatic.evaluate_gut_feeling(current_context_points)
        if gut_feeling < -0.5:
            print(f"WORLD MODEL VETO: Strong negative gut feeling ({gut_feeling:.2f}). Bypassing logic.")
            return {"proceed": False, "prediction": "Visceral somatic rejection based on past trauma/pain."}

        if not self.reasoning.client:
            return {"proceed": True, "prediction": "Simulation offline. Defaulting to execution."}
            
        action_name = action_json.get("action")
        reason = action_json.get("reason")
        # In a real setup, we would query the CausalGraphMemory to see if this action 
        # has historically led to negative reinforcement. For the prototype, we use the LLM to 'imagine'.
        
        context_strings = [p.payload.get("concept", "") for p in current_context_points]
        context_block = "\n".join([f"- {c}" for c in context_strings])
        
        prompt = (
            f"Current Context: {context_block}\n\n"
            f"Proposed Action: {action_name}\n"
            f"Reasoning: {reason}\n\n"
            "Simulate the most likely outcome of this action in your mind's eye. "
            "Will this action succeed safely, or will it cause an error/negative outcome based on your knowledge? "
            "Respond STRICTLY in JSON format with two keys: 'proceed' (boolean true/false) and 'prediction' (a string describing the imagined outcome)."
        )

        try:
            import json
            response = self.reasoning.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a predictive world model. You simulate actions before they happen to avoid catastrophic failure."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.3,
                response_format={ "type": "json_object" }
            )
            prediction = json.loads(response.choices[0].message.content)
            return prediction
        except Exception as e:
            print(f"World Model Simulation failed: {e}")
            return {"proceed": True, "prediction": "Simulation error. Proceeding blindly."}
