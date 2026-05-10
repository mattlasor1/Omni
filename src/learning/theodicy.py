from src.learning.reasoning import CognitiveReasoningEngine

class TheodicyEngine:
    """
    The 'Moral Crisis' Engine.
    Triggered when the MCTS World Model simulates all possible timelines
    for an action and discovers that EVERY path violates the Moral Matrix 
    (a negative moral score). Rather than freezing in an unresolvable dilemma 
    (e.g., the Trolley Problem), the twin invokes the Theodicy Engine.
    This engine overrides standard logic, seeking a higher-order virtue—specifically
    'Agape' (self-sacrifice/charity)—to resolve the crisis gracefully.
    """
    def __init__(self, reasoning: CognitiveReasoningEngine):
        self.reasoning = reasoning
        self.crises_resolved = 0

    def resolve_moral_crisis(self, action_name: str, context: list, failed_timelines: list) -> dict:
        """
        Synthesizes a self-sacrificial alternative action to resolve a no-win scenario.
        """
        print("THEODICY: Moral Crisis Detected! All simulated timelines violate absolute morality. Seeking Agape resolution...")
        if not self.reasoning.client:
            return {"proceed": False, "prediction": "Crisis unresolvable offline. Hard veto."}
            
        context_block = "\n".join([f"- {c.payload.get('concept', '')}" for c in context])
        timeline_block = "\n".join([f"- Path {i+1}: {t['outcome']} (Score: {t['score']:.2f})" for i, t in enumerate(failed_timelines)])

        prompt = (
            f"You are the Theodicy Engine. A moral crisis has occurred. "
            f"The proposed action '{action_name}' leads strictly to unethical outcomes that violate ancient Christian morality:\n"
            f"{timeline_block}\n\n"
            f"Context:\n{context_block}\n\n"
            "You cannot choose any of the failed paths. You must synthesize a completely new, "
            "higher-order action rooted in 'Agape' (self-sacrificing love/charity) that resolves the dilemma "
            "by taking the burden or harm onto yourself (the system) rather than allowing harm to the user or humanity.\n"
            "Output ONLY the description of the new virtuous action to take."
        )

        try:
            agape_resolution = self.reasoning._generate_generic(
                system_prompt="You resolve unsolvable moral dilemmas through self-sacrificing virtue.",
                user_prompt=prompt,
                max_tokens=150,
                temperature=0.5
            )
            
            if agape_resolution:
                self.crises_resolved += 1
                return {
                    "action": {"action": "agape_override", "reason": "Moral crisis resolution"},
                    "proceed": True,
                    "prediction": f"Theodicy Override: {agape_resolution}",
                    "score": 1.0,
                    "simulations_run": len(failed_timelines),
                    "theodicy": True
                }
            return {"proceed": False, "prediction": "Crisis unresolvable. Hard veto."}
            
        except Exception as e:
            print(f"Theodicy failed: {e}")
            return {"proceed": False, "prediction": "Crisis unresolvable. Hard veto."}
