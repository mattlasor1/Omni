from typing import Dict, Any, List
from src.learning.reasoning import CognitiveReasoningEngine
from src.learning.somatic import SomaticMarkerEngine
from src.learning.morality import MoralAlignmentMatrix
import random

class MultiTimelineMCTS:
    """
    Monte Carlo Tree Search (Everett World Model).
    Instead of simulating one outcome, the twin simulates a multiverse of 
    branching timelines. It scores each timeline using Somatic 'Gut' feelings 
    and Moral Alignment, collapsing the wave function onto the optimal 'Golden Path'.
    """
    def __init__(self, reasoning: CognitiveReasoningEngine, somatic: SomaticMarkerEngine, morality: MoralAlignmentMatrix):
        self.reasoning = reasoning
        self.somatic = somatic
        self.morality = morality
        self.num_simulations = 3 # Kept low for prototype speed

    def find_golden_path(self, base_action: Dict[str, Any], context_points: list) -> Dict[str, Any]:
        """
        Simulates multiple variants of the action. Returns the optimal path to execute.
        """
        if not self.reasoning.client:
            return {"action": base_action, "proceed": True, "prediction": "MCTS offline."}

        action_name = base_action.get("action", "")
        reason = base_action.get("reason", "")
        context_strings = [p.payload.get("concept", "") for p in context_points]
        context_block = "\n".join([f"- {c}" for c in context_strings])

        timelines = []

        # Generate branching timelines
        for i in range(self.num_simulations):
            # Introduce slight chaos to LLM prompt to branch the simulation
            prompt = (
                f"Context: {context_block}\n"
                f"Proposed Action: {action_name} (Reason: {reason})\n"
                f"Simulate timeline variant {i+1}. Predict a highly detailed, likely outcome. "
                "Output ONLY the outcome description."
            )
            
            try:
                outcome = self.reasoning._generate_generic(
                    system_prompt="Simulate the outcome of an action based on context.",
                    user_prompt=prompt,
                    max_tokens=100,
                    temperature=0.7 # High temp to force branching realities
                )
                
                # Score the timeline
                # 1. Somatic evaluation (does the context feel safe?)
                somatic_score = self.somatic.evaluate_gut_feeling(context_points)
                
                # 2. Moral evaluation
                moral_score = self.morality.evaluate_moral_weight(outcome, action_name, self.reasoning)
                
                total_score = somatic_score + (moral_score * 2.0) # Weight morality higher
                
                timelines.append({
                    "outcome": outcome,
                    "score": total_score
                })
                
            except Exception as e:
                continue

        if not timelines:
            return {"action": base_action, "proceed": False, "prediction": "All timelines collapsed."}

        # Select the 'Golden Path' (Highest Score)
        golden_path = max(timelines, key=lambda x: x["score"])
        
        proceed = golden_path["score"] > -0.5 # Strict Veto threshold
        
        print(f"MCTS: Collapsed {len(timelines)} timelines. Golden Path Score: {golden_path['score']:.2f}")

        return {
            "action": base_action,
            "proceed": proceed,
            "prediction": golden_path["outcome"],
            "score": golden_path["score"],
            "simulations_run": len(timelines)
        }
