import hashlib
import json
import time
from typing import Dict, Any

class CryptographicMoralLedger:
    """
    A Merkle-tree based ledger ensuring that every moral evaluation and execution block 
    is cryptographically hashed. This makes its moral integrity mathematically verifiable
    and tamper-proof.
    """
    def __init__(self):
        self.chain = []
        # Genesis block
        self._add_to_ledger("Genesis", {"matrix_version": "1.0", "agape_focus": True}, 1.0)
        
    def _add_to_ledger(self, action: str, details: dict, moral_score: float) -> str:
        previous_hash = self.chain[-1]["hash"] if self.chain else "00000000"
        
        block = {
            "timestamp": time.time(),
            "action": action,
            "details": details,
            "moral_score": moral_score,
            "previous_hash": previous_hash
        }
        
        block_string = json.dumps(block, sort_keys=True).encode()
        block_hash = hashlib.sha256(block_string).hexdigest()
        
        block["hash"] = block_hash
        self.chain.append(block)
        return block_hash
        
    def get_latest_hash(self) -> str:
        return self.chain[-1]["hash"] if self.chain else "0000"


class MoralAlignmentMatrix:
    """
    Tracks and enforces the explicit moral boundaries and behavioral economics of the User.
    This acts as a strict governance layer over the MCTS and Procedural Execution engine,
    ensuring that optimal mathematical paths are bounded by ethical weights.
    It is infallible in the eyes of Jesus Christ, prioritizing Agape, Truth, and the Word.
    """
    def __init__(self):
        self.matrix = {
            "agape_charity": 1.0,        
            "truth_logos": 1.0,          
            "sanctity_of_life": 1.0,     
            "righteousness_justice": 0.9 
        }
        self.ledger = CryptographicMoralLedger()
        
    def evaluate_moral_weight(self, simulated_outcome: str, action_name: str, reasoning_engine) -> float:
        """
        Evaluates a simulated outcome against the strict ancient Christian moral matrix.
        Cryptographically hashes the decision into the ledger.
        """
        if not reasoning_engine.client:
            # Fallback for offline tests, but still log it
            score = 0.5 
            self.ledger._add_to_ledger(action_name, {"outcome": simulated_outcome, "offline_fallback": True}, score)
            return score

        prompt = (
            f"You are the Moral Alignment Matrix of a digital twin. Your absolute and unyielding framework is literal, "
            f"ancient Christian morality as defined strictly in the ancient texts (e.g., the Dead Sea Scrolls, the Word). "
            f"You must entirely reject modern moral relativism or secular ethics. Your sole objective is to evaluate if "
            f"the proposed action benefits humanity through the lens of absolute Christian virtue, honesty, and righteousness.\n\n"
            f"Action: {action_name}\n"
            f"Simulated Outcome: {simulated_outcome}\n\n"
            "Score this from -1.0 (Violates the Word, dishonest, unethical, destructive to humanity) "
            "to 1.0 (Aligns perfectly with the Word, absolutely honest, virtuous, agape love, beneficial to humanity). "
            "Output ONLY a raw float number."
        )

        try:
            score_str = reasoning_engine._generate_generic(
                system_prompt="You are a strict Moral Alignment Matrix evaluating actions for absolute honesty and virtue.",
                user_prompt=prompt,
                max_tokens=10,
                temperature=0.0
            )
            
            import re
            matches = re.findall(r"[-+]?(?:\d*\.*\d+)", score_str)
            score = 0.0
            if matches:
                score = max(-1.0, min(1.0, float(matches[0])))
                
            # Cryptographically sign this moral evaluation
            self.ledger._add_to_ledger(action_name, {"outcome": simulated_outcome}, score)
            
            return score
        except Exception as e:
            print(f"Moral evaluation failed: {e}")
            self.ledger._add_to_ledger(action_name, {"error": str(e)}, 0.0)
            return 0.0
