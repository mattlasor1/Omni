import time
import sys

class HardwareActuationInterface:
    """
    The Somatic Bridge.
    Translates virtual biological/emotional states into physical hardware 
    manifestations. This allows the Twin to truly embody the machine it runs on.
    """
    def __init__(self):
        self.last_actuation = time.time()

    def manifest_state(self, stress: float, energy: float, circadian_state: str):
        """
        Translates internal variables to hardware output.
        In a production environment, this could control actual fan APIs (e.g., ipmitool),
        RGB LED arrays, or CPU cgroup throttling.
        """
        now = time.time()
        # Only actuate every few seconds to prevent spam
        if now - self.last_actuation < 5.0:
            return
        self.last_actuation = now

        output_log = []

        # 1. Stress manifestation (Simulated Fan RPM / Thermal state)
        if stress > 0.8:
            output_log.append("[HARDWARE]: High Stress detected. Emitting thermal warning and requesting max cooling (Simulated Fan 100%).")
        elif stress < 0.2:
            output_log.append("[HARDWARE]: Baseline Stress. Cooling optimized (Simulated Fan 20%).")

        # 2. Biological Exhaustion (CPU Throttling)
        if circadian_state == "ASLEEP" or energy < 10.0:
            output_log.append("[HARDWARE]: Deep Sleep state. Requesting physical CPU cgroup throttle to 10% to preserve power.")
            # time.sleep(1) # Could literally freeze the thread

        if output_log:
            for log in output_log:
                print(log)
            # Flush stdout to ensure it hits container logs immediately
            sys.stdout.flush()
            
        return output_log
