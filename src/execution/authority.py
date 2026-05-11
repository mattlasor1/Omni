from typing import Dict, Any

class TrustAndAuthorityProtocol:
    """
    The Dynamic Authority Matrix.
    Determines if the Twin has the autonomy to execute an action immediately
    or if it must halt and ask the user for explicit cryptographic approval.
    Calculated via the MCTS simulation score (risk) vs. Bayesian Confidence.
    """
    def __init__(self):
        # A simple in-memory queue for actions awaiting user approval
        self.pending_actions: Dict[str, Dict[str, Any]] = {}

    def evaluate_authority(self, mcts_prediction: dict, avg_bayesian_belief: float) -> bool:
        """
        Returns True if the Twin has authority to execute.
        Returns False if it must queue the action for user approval.
        """
        score = mcts_prediction.get("score", 0.0)
        
        # High Risk Action (Score near threshold) but low epistemic belief
        if score < 0.5 and avg_bayesian_belief < 0.8:
            return False # Strip authority, require human
            
        # Action is very safe, or we are absolutely certain
        return True

    def queue_action(self, action_id: str, action_data: dict):
        """Holds an action in stasis until human approval."""
        self.pending_actions[action_id] = action_data
        print(f"AUTHORITY: High risk/low confidence detected. Action {action_id} queued for human approval.")

    def approve_action(self, action_id: str) -> dict:
        """User approves."""
        if action_id in self.pending_actions:
            return self.pending_actions.pop(action_id)
        return {}

    def reject_action(self, action_id: str) -> bool:
        """User rejects."""
        if action_id in self.pending_actions:
            del self.pending_actions[action_id]
            return True
        return False
        
    def get_pending_queue(self) -> list:
        return [{"id": k, "action": v.get("action")} for k, v in self.pending_actions.items()]
