from src.learning.engine import ParameterExtractor
import numpy as np

class ThalamicGate:
    """
    The Subconscious Filter.
    The human brain receives ~11 million bits of sensory data per second but
    only consciously processes ~50. The Thalamic Gate mathematically evaluates 
    incoming raw signals. If a signal lacks sufficient magnitude, novelty, 
    or emotional salience, it is immediately discarded (forgotten before it is ever cached).
    """
    def __init__(self, extractor: ParameterExtractor):
        self.extractor = extractor
        self.salience_threshold = 0.4 # Minimum magnitude/novelty required to pass
        self.filtered_count = 0
        self.passed_count = 0

    def evaluate_signal(self, data_type: str, content: str, internal_arousal: float) -> bool:
        """
        Evaluates whether an incoming signal deserves conscious processing.
        Returns True if it passes the gate, False if it is rejected as noise.
        """
        try:
            # 1. Very rapid, shallow parameter extraction to test magnitude
            shallow_params = self.extractor.extract(data_type, content)
            magnitude = np.linalg.norm(shallow_params)
            
            # 2. Dynamic Threshholding based on Arousal
            # If the twin is highly aroused (panicked/excited), the gate opens wider (lower threshold).
            # If the twin is calm, the gate restricts to only highly salient data.
            dynamic_threshold = self.salience_threshold * (1.0 - (internal_arousal * 0.5))
            
            # Simulated heuristic: In a real model, we compare against a rolling baseline of noise.
            # Here, we use string entropy as a proxy for signal density.
            char_set = set(content)
            entropy = len(char_set) / max(len(content), 1)
            
            salience_score = (magnitude * 0.1) + (entropy * 0.9)
            
            if salience_score > dynamic_threshold:
                self.passed_count += 1
                return True
            else:
                self.filtered_count += 1
                return False
                
        except Exception as e:
            # If we can't parse it quickly, reject it to protect the system
            self.filtered_count += 1
            return False

    def get_filter_ratio(self) -> float:
        total = self.filtered_count + self.passed_count
        if total == 0: return 0.0
        return (self.filtered_count / total) * 100.0
