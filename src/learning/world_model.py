from typing import Dict, Any
from src.learning.reasoning import CognitiveReasoningEngine
from src.memory.graph_db import CausalGraphMemory
from src.learning.somatic import SomaticMarkerEngine
from src.learning.morality import MoralAlignmentMatrix
from src.learning.mcts import MultiTimelineMCTS

class PredictiveWorldModel:
    """
    The 'Mind's Eye' or Imagination of the Digital Twin.
    Replaced simple simulation with Multi-Timeline MCTS. Before acting, 
    the twin simulates thousands of branching futures, evaluates their moral 
    and somatic outcomes, and collapses the wave function into the optimal choice.
    """
    def __init__(self, reasoning: CognitiveReasoningEngine, causal_graph: CausalGraphMemory, somatic: SomaticMarkerEngine, morality: MoralAlignmentMatrix):
        self.reasoning = reasoning
        self.graph = causal_graph
        self.somatic = somatic
        self.morality = morality
        self.mcts = MultiTimelineMCTS(reasoning, somatic, morality)

    def simulate_action(self, action_json: Dict[str, Any], current_context_points: list) -> Dict[str, Any]:
        """
        Runs the MCTS branching simulation.
        """
        # 1. System 1 Somatic Pre-Check (Fast Veto)
        gut_feeling = self.somatic.evaluate_gut_feeling(current_context_points)
        if gut_feeling < -0.8:
            print(f"WORLD MODEL VETO: Extreme negative gut feeling ({gut_feeling:.2f}).")
            return {"proceed": False, "prediction": "Visceral somatic rejection."}

        # 2. Invoke MCTS (System 2 Multi-Timeline Simulation)
        golden_path = self.mcts.find_golden_path(action_json, current_context_points)
        
        return golden_path
