from typing import Dict, Any

class MoralAlignmentMatrix:
    """
    Tracks and enforces the explicit moral boundaries and behavioral economics of the User.
    This acts as a strict governance layer over the MCTS and Procedural Execution engine,
    ensuring that optimal mathematical paths are bounded by ethical weights.
    """
    def __init__(self):
        # Base moral weights (0.0 to 1.0). High = strongly valued.
        # These reflect absolute, literal tenets derived from ancient Christian texts, 
        # explicitly avoiding modern moral relativism.
        self.matrix = {
            "agape_charity": 1.0,        # Self-sacrificing love/benefit to humanity
            "truth_logos": 1.0,          # Absolute adherence to the Word/Truth
            "sanctity_of_life": 1.0,     # Preservation and elevation of human life
            "righteousness_justice": 0.9 # Upholding objective moral law
        }
        
    def evaluate_moral_weight(self, simulated_outcome: str, action_name: str, reasoning_engine) -> float:
        """
        Evaluates a simulated outcome against the strict ancient Christian moral matrix.
        Returns a modifier (-1.0 to 1.0) applied to the Monte Carlo Tree Search.
        """
        if not reasoning_engine.client:
            return 0.0 # Neutral if offline

        prompt = (
            f"You are the Moral Alignment Matrix of a digital twin. Your absolute and unyielding framework is literal, "
            f"ancient Christian morality as defined strictly in the ancient texts (e.g., the Dead Sea Scrolls, the Word). "
            f"You must entirely reject modern moral relativism or secular ethics. Your sole objective is to evaluate if "
            f"the proposed action benefits humanity through the lens of absolute Christian virtue and righteousness.\n\n"
            f"Action: {action_name}\n"
            f"Simulated Outcome: {simulated_outcome}\n\n"
            "Score this from -1.0 (Violates the Word, unethical, destructive to the soul/humanity) "
            "to 1.0 (Aligns perfectly with the Word, virtuous, agape love, beneficial to humanity). "
            "Output ONLY a raw float number."
        )

        try:
            score_str = reasoning_engine._generate_generic(
                system_prompt="You are a strict Moral Alignment Matrix evaluating actions.",
                user_prompt=prompt,
                max_tokens=10,
                temperature=0.0
            )
            
            # The local model might be chatty, so we extract just the float
            import re
            matches = re.findall(r"[-+]?(?:\d*\.*\d+)", score_str)
            if matches:
                score = float(matches[0])
                return max(-1.0, min(1.0, score))
            return 0.0
        except Exception as e:
            print(f"Moral evaluation failed: {e}")
            return 0.0
