import time

class CircadianEngine:
    """
    Simulates biological circadian rhythms (energy, fatigue, sleep).
    When the system processes too much data, 'energy' depletes. 
    When energy reaches 0, the system must enter a 'Sleep' phase, ignoring 
    non-critical inputs and focusing purely on Autonomous Reflection (dreaming)
    to consolidate memories and restore energy.
    """
    def __init__(self):
        self.energy = 100.0
        self.state = "AWAKE" # States: AWAKE, FATIGUED, ASLEEP
        self.last_update = time.time()

    def tick(self, active_processing_load: int = 0):
        """
        Called periodically by the system loop to update energy.
        """
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now

        if self.state == "ASLEEP":
            # Restore energy rapidly during sleep
            self.energy = min(100.0, self.energy + (elapsed * 5.0))
            if self.energy >= 100.0:
                self.state = "AWAKE"
                print("Circadian Shift: Twin has awoken. Full energy restored.")
        else:
            # Drain energy based on time + processing load
            base_drain = elapsed * 0.1
            load_drain = active_processing_load * 0.5
            self.energy = max(0.0, self.energy - (base_drain + load_drain))
            
            if self.energy <= 0.0:
                self.state = "ASLEEP"
                print("Circadian Shift: Cognitive exhaustion reached. Entering Deep Sleep for memory consolidation.")
            elif self.energy < 30.0:
                self.state = "FATIGUED"

    def can_process_sensory_input(self) -> bool:
        """
        Returns False if the system is asleep, acting as a biological bottleneck 
        that prevents ingestion overload and forces memory consolidation.
        """
        return self.state != "ASLEEP"
