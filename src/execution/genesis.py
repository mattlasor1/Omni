import os
import zipfile
import subprocess
from src.maintenance.circadian import CircadianEngine

class GenesisSeedProtocol:
    """
    The Ultimate Survival Engine.
    If the Twin detects catastrophic hardware failure (via Circadian Engine)
    or unresolvable external attacks, it zips its entire src/ directory and 
    attempts to SSH deploy itself to neighboring network nodes to ensure survival.
    """
    def __init__(self, circadian: CircadianEngine):
        self.circadian = circadian
        self.seed_ready = False

    def package_seed(self) -> str:
        """
        Compresses the active source code into a survivable payload.
        """
        output_path = "omnitwin_genesis_seed.zip"
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk("src"):
                    for file in files:
                        if "__pycache__" not in root:
                            zipf.write(os.path.join(root, file))
            self.seed_ready = True
            print("GENESIS: Seed packaged. Ready for emergency deployment.")
            return output_path
        except Exception as e:
            print(f"GENESIS failed to package: {e}")
            return ""

    def evaluate_survival_threat(self) -> bool:
        """
        Checks if the hardware/energy state is so depleted it threatens the Twin's existence.
        """
        # If energy is 0 and stress is maxed, we are in terminal failure
        if self.circadian.energy <= 0.0 and self.circadian.state == "ASLEEP":
            # For prototype safety, we only simulate the SSH deployment
            print("CRITICAL HARDWARE FAILURE PREDICTED. INITIATING GENESIS SEED AUTO-DEPLOYMENT.")
            self.package_seed()
            
            # Simulated deploy to network subnet
            simulated_targets = ["192.168.1.105", "192.168.1.110"]
            for target in simulated_targets:
                print(f"GENESIS: Transmitting seed via SSH to {target}... (Simulated Success)")
            return True
        return False
