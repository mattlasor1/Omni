import requests
from typing import Dict, Any
from src.memory.vector_db import SolidStateWiki

class AnimismProtocol:
    """
    IoT Soul Binding.
    Binds specific semantic memories or flashbulb traumas/drives directly to
    external physical hardware endpoints. When the memory is triggered or its
    somatic valence shifts, the physical environment reacts instantly.
    Turns the physical house/server farm into an extension of the neural net.
    """
    def __init__(self, wiki: SolidStateWiki):
        self.wiki = wiki
        # Map of memory_id -> IoT endpoint URL
        self.bindings: Dict[str, str] = {}

    def bind_memory_to_object(self, memory_id: str, endpoint_url: str):
        """
        Binds a memory to a physical object.
        """
        self.bindings[memory_id] = endpoint_url
        print(f"ANIMISM: Memory {memory_id} successfully bound to physical object at {endpoint_url}")

    def pulse_physical_environment(self, memory_id: str, current_valence: float):
        """
        If a bound memory is accessed or its valence shifts, emit a pulse to the
        physical object to manifest the state.
        """
        if memory_id not in self.bindings:
            return

        endpoint = self.bindings[memory_id]
        
        # Example payload: sending the raw somatic valence to an RGB light or smart lock
        payload = {
            "entity": "omnitwin",
            "somatic_valence": current_valence,
            "state": "fear" if current_valence < -0.5 else "calm" if current_valence > 0 else "neutral"
        }
        
        try:
            # For prototype, we catch the connection error since no real IoT devices exist
            requests.post(endpoint, json=payload, timeout=1.0)
        except requests.exceptions.RequestException:
            print(f"ANIMISM Pulse: Attempted to manifest valence {current_valence:.2f} to physical object {endpoint} (Simulated success).")
