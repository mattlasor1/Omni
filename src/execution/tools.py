import time
from typing import Dict, Any

class ExecutionRouter:
    """
    The 'Hands' of the Digital Twin.
    Takes the structured JSON output from the ProceduralActionEngine and 
    attempts to execute it in the real (or simulated) environment.
    """
    def __init__(self, cache_interface):
        self.cache = cache_interface

    def execute_action(self, action_json: Dict[str, Any]) -> str:
        """
        Routes the action to the appropriate tool.
        Returns a string representing the result/observation of the action.
        """
        action = action_json.get("action", "none")
        reason = action_json.get("reason", "unknown")
        
        print(f"Executing Action: {action} (Reason: {reason})")
        
        result_observation = ""
        
        if action == "none":
            result_observation = "Decided to take no action."
            
        elif action.startswith("search:"):
            query = action.split("search:")[1]
            # Simulated tool: Web Search
            result_observation = f"Searched for '{query}'. Found 3 relevant simulated results."
            
        elif action.startswith("log:"):
            msg = action.split("log:")[1]
            # Simulated tool: System Logging
            result_observation = f"Logged message to system: '{msg}'"
            
        else:
            result_observation = f"Attempted unknown action '{action}'. Execution failed."

        # Feedback Loop: Feed the result back into the sensory cache
        # so the twin 'observes' the result of its own action.
        self._feed_observation_to_cache(action, result_observation)
        
        return result_observation

    def _feed_observation_to_cache(self, action_taken: str, observation: str):
        if self.cache:
            payload = {
                "type": "text",
                "source_id": "internal_execution_engine",
                "content": f"I took action '{action_taken}'. The result was: {observation}",
                "timestamp": time.time()
            }
            self.cache.add_to_stream(payload)
            print("Action observation fed back into sensory stream.")
