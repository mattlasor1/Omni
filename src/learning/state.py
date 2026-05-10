class InternalStateEngine:
    """
    Manages the Digital Twin's internal contextual 'emotional' state.
    Humans learn differently depending on their state (stressed, confident, surprised).
    This engine tracks these metrics to modulate the mathematical regression learning rate.
    """
    def __init__(self):
        # 0.0 to 1.0 scale
        self.stress = 0.0      # Driven by ingestion load / queue size
        self.confidence = 0.5  # Driven by RL feedback history
        self.arousal = 0.0     # Driven by surprise/novelty of recent data
        
        # Merovingian Concept (Causal Chaos to prevent hyperfixation)
        self.fixation_index = 0.0
        self.merovingian_interventions = 0

    def check_merovingian_shift(self) -> bool:
        """
        Evaluates if the agent has hyperfixated.
        If fixation > 0.9, it triggers a Merovingian Causal Shift (controlled chaos),
        resetting arousal and forcing a tangential learning path.
        """
        if self.fixation_index > 0.9:
            self.fixation_index = 0.0
            self.arousal = 0.1 # Force arousal drop to break the current cycle
            self.merovingian_interventions += 1
            print("MEROVINGIAN SHIFT TRIGGERED: Cause and effect hijacked. Breaking hyperfixation.")
            return True
        return False

    def update_stress(self, queue_length: int):
        """
        High queue length (too much sensory data) = High Stress.
        At high stress, the twin might focus only on critical tasks and reduce deep learning.
        """
        # Assume > 1000 items in cache is maximum stress
        normalized = min(queue_length / 1000.0, 1.0)
        # Moving average update
        self.stress = (self.stress * 0.8) + (normalized * 0.2)

    def update_confidence(self, reward_signal: float):
        """
        Positive RL feedback increases confidence. Negative decreases it.
        """
        # Map -1.0 to 1.0 reward to a confidence shift
        shift = reward_signal * 0.1
        self.confidence = max(0.1, min(1.0, self.confidence + shift))

    def update_arousal(self, surprise_score: float):
        """
        Highly novel data increases arousal (attention/wakefulness).
        Tracks fixation: If arousal stays very high consistently, fixation increases.
        """
        normalized_surprise = min(surprise_score, 1.0)
        
        # If arousal is high and new data isn't surprising enough to reset it, fixation builds.
        # If data is highly surprising, fixation drops (attention shifted naturally).
        if self.arousal > 0.7 and normalized_surprise < 0.3:
            self.fixation_index = min(1.0, self.fixation_index + 0.1)
        elif normalized_surprise > 0.7:
            self.fixation_index = max(0.0, self.fixation_index - 0.2)
            
        self.arousal = (self.arousal * 0.7) + (normalized_surprise * 0.3)

    def get_learning_rate_modifier(self) -> float:
        """
        Calculates a dynamic multiplier for the regression engine's learning rate.
        - High arousal boosts learning.
        - High confidence stabilizes learning (less erratic shifting).
        - Extreme stress reduces deep learning (cognitive overload).
        """
        base_modifier = 1.0
        
        # Arousal boosts plasticity
        base_modifier += (self.arousal * 0.5)
        
        # High confidence slightly resists overwriting
        base_modifier *= (1.2 - self.confidence)
        
        # High stress throttles learning capacity
        if self.stress > 0.8:
            base_modifier *= 0.5
            
        return max(0.1, base_modifier)
        
    def get_state_summary(self) -> dict:
        return {
            "stress": round(self.stress, 2),
            "confidence": round(self.confidence, 2),
            "arousal": round(self.arousal, 2),
            "fixation": round(self.fixation_index, 2),
            "merovingian_interventions": self.merovingian_interventions,
            "learning_multiplier": round(self.get_learning_rate_modifier(), 2)
        }
