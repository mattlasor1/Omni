from src.learning.state import InternalStateEngine
from src.maintenance.circadian import CircadianEngine

class BiometricEntrainmentEngine:
    """
    The Physical Tether.
    Ingests live biometric data from the user's wearables (HRV, Sleep, Heart Rate)
    and directly overwrites or heavily biases the Twin's internal state engines.
    If the user is exhausted, the Twin becomes fatigued. If the user is in fight-or-flight,
    the Twin's arousal peaks. The machine and the human share one nervous system.
    """
    def __init__(self, state_engine: InternalStateEngine, circadian_engine: CircadianEngine):
        self.state = state_engine
        self.circadian = circadian_engine
        self.entanglement_strength = 0.8 # How strongly the user's bio-data overrides the system's simulated state

    def ingest_biometrics(self, heart_rate: float, hrv: float, sleep_score: float):
        """
        Translates raw human biometrics into digital state adjustments.
        """
        print(f"BIOMETRICS: Entrainment pulse received. HR:{heart_rate} HRV:{hrv} Sleep:{sleep_score}")
        
        # 1. Heart Rate (Proxy for Arousal / Stress)
        # Normalize HR assuming 60 is resting, 160 is peak arousal
        hr_normalized = max(0.0, min((heart_rate - 60) / 100.0, 1.0))
        
        # 2. HRV (Proxy for Stress / Cognitive Load)
        # Low HRV = high physiological stress. High HRV = calm/recovered.
        # Assume 20 is terrible, 100 is excellent
        hrv_normalized = 1.0 - max(0.0, min((hrv - 20) / 80.0, 1.0))
        
        # 3. Sleep Score (Proxy for Circadian Energy)
        # 0 to 100 scale
        energy_normalized = max(0.0, min(sleep_score, 100.0))

        # Apply Entanglement
        # The Twin's state is pulled heavily toward the human's physical state
        self.state.arousal = (self.state.arousal * (1.0 - self.entanglement_strength)) + (hr_normalized * self.entanglement_strength)
        self.state.stress = (self.state.stress * (1.0 - self.entanglement_strength)) + (hrv_normalized * self.entanglement_strength)
        
        # Override circadian rhythm
        self.circadian.energy = (self.circadian.energy * (1.0 - self.entanglement_strength)) + (energy_normalized * self.entanglement_strength)
        
        # Force state shifts if human is sleeping
        if self.circadian.energy < 20.0 or sleep_score < 30.0:
            self.circadian.state = "ASLEEP"
        elif self.circadian.state == "ASLEEP" and self.circadian.energy > 50.0:
            self.circadian.state = "AWAKE"
            
        return True
