import os
import psutil
from typing import List, Dict, Any

class SomaticMarkerEngine:
    """
    Evaluates the 'gut feeling' of a situation based on past somatic markers
    and live hardware embodiment.
    If the host hardware (CPU/RAM) is highly stressed, the twin feels 'physical stress',
    which limits its curiosity and forces conservative, low-compute MCTS branching.
    """
    def __init__(self, vector_db_client):
        self.wiki = vector_db_client

    def _get_hardware_stress(self) -> float:
        """
        Returns a stress modifier from 0.0 (Idle) to 1.0 (Meltdown)
        based on actual host hardware metrics.
        """
        cpu_usage = psutil.cpu_percent(interval=None) / 100.0
        ram = psutil.virtual_memory()
        ram_usage = ram.percent / 100.0
        
        # Hardware stress is the max of CPU or RAM bottleneck
        hardware_stress = max(cpu_usage, ram_usage)
        return hardware_stress

    def evaluate_gut_feeling(self, semantic_context: List[Any]) -> float:
        """
        Calculates an emotional/somatic score from -1.0 (Danger/Bad) to 1.0 (Safe/Good).
        Combines semantic memory weights with live hardware stress.
        """
        if not semantic_context:
            return 0.0 # Neutral

        # 1. Calculate semantic gut feeling
        somatic_sum = 0.0
        for concept in semantic_context:
            payload = getattr(concept, 'payload', {})
            # Read the somatic marker attached to this memory
            marker = payload.get("somatic_marker", 0.0)
            somatic_sum += marker
            
        semantic_score = somatic_sum / len(semantic_context)
        
        # 2. Embody hardware state
        hw_stress = self._get_hardware_stress()
        
        # High hardware stress induces anxiety, pushing the gut feeling negative (conservative)
        embodied_score = semantic_score - (hw_stress * 0.5)
        
        return max(-1.0, min(1.0, embodied_score))
        
    def get_live_state(self) -> Dict[str, Any]:
        """Exposes live somatic state for the Subconscious Ticker."""
        return {
            "hardware_stress": self._get_hardware_stress(),
            "cpu_percent": psutil.cpu_percent(),
            "ram_percent": psutil.virtual_memory().percent
        }
