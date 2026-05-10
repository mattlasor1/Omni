from typing import Dict, Any
from src.learning.reasoning import CognitiveReasoningEngine
from src.memory.graph_db import CausalGraphMemory

class PredictiveWorldModel:
    """
    The 'Mind's Eye' or Imagination of the Digital Twin.
    Before taking an action, this engine simulates the action against the 
    causal graph and semantic memory to predict the outcome. If the simulated
    outcome is highly negative or illogical, it vetos the action.
    """
    def __init__(self, reasoning: CognitiveReasoningEngine, causal_graph: CausalGraphMemory):
        self.reasoning = reasoning
        self.graph = causal_graph

    def simulate_action(self, action_json: Dict[str, Any], current_context: list[str]) -> Dict[str, Any]:
        """
        Simulates an action and returns a prediction and a go/no-go decision.
        """
        if not self.reasoning.client:
            return {"proceed": True, "prediction": "Simulation offline. Defaulting to execution."}
            
        action_name = action_json.get("action")
        reason = action_json.get("reason")
        
        # In a real setup, we would query the CausalGraphMemory to see if this action 
        # has historically led to negative reinforcement. For the prototype, we use the LLM to 'imagine'.
        
        context_block = "\n".join([f"- {c}" for c in current_context])
        
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
