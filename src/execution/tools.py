import time
from typing import Dict, Any
from src.execution.meta_learning import MetaLearningEngine

class ExecutionRouter:
    """
    The 'Hands' of the Digital Twin.
    Takes the structured JSON output from the ProceduralActionEngine and 
    attempts to execute it in the real (or simulated) environment.
    Includes dynamically evolved tools via MetaLearningEngine.
    """
    def __init__(self, cache_interface, meta_learning: MetaLearningEngine = None):
        self.cache = cache_interface
        self.meta = meta_learning

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
            
        elif action.startswith("evolve:"):
            capability = action.split("evolve:")[1]
            if self.meta:
                success = self.meta.evolve_new_tool(capability)
                result_observation = f"Evolution attempt for '{capability}': {'Success' if success else 'Failed'}"
            else:
                result_observation = "Meta-Learning engine offline."
                
        else:
            # Check if it's a dynamic meta-tool
            if self.meta and action in self.meta.dynamic_tools:
                try:
                    result_observation = self.meta.dynamic_tools[action]("")
                except Exception as e:
                    result_observation = f"Dynamic execution failed: {e}"
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
