import math
from typing import Dict, Any, List, Tuple
import json

class SpatialMemoryManifold:
    """
    4D Spatial-Temporal Memory Engine.
    Allows the twin to map its semantic and episodic intelligence onto physical
    geometry (x, y, z coordinates) and time (t). Enables connection to real-world
    IoT, drone arrays, or physical spaces.
    """
    def __init__(self):
        # A simple in-memory 4D manifold representation for the prototype.
        # Maps geometric coordinate blocks to specific semantic memory IDs.
        self.manifold: Dict[Tuple[float, float, float], List[str]] = {}
        self.resolution = 1.0 # 1-meter or 1-unit cubic grid resolution

    def _quantize_coords(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        """Snaps a precise coordinate to the nearest grid resolution block."""
        return (
            round(x / self.resolution) * self.resolution,
            round(y / self.resolution) * self.resolution,
            round(z / self.resolution) * self.resolution
        )

    def map_memory(self, memory_id: str, x: float, y: float, z: float):
        """
        Binds a memory to a physical location in the Twin's internal world map.
        """
        coord = self._quantize_coords(x, y, z)
        if coord not in self.manifold:
            self.manifold[coord] = []
        if memory_id not in self.manifold[coord]:
            self.manifold[coord].append(memory_id)

    def query_spatial_radius(self, x: float, y: float, z: float, radius: float) -> List[str]:
        """
        Returns all memory IDs that occurred within a given physical radius.
        Allows the twin to answer: "What happened here?" or "What do I know about this room?"
        """
        found_memories = []
        center = (x, y, z)
        
        for coord, memories in self.manifold.items():
            dist = math.sqrt(
                (coord[0] - center[0])**2 + 
                (coord[1] - center[1])**2 + 
                (coord[2] - center[2])**2
            )
            if dist <= radius:
                found_memories.extend(memories)
                
        return list(set(found_memories))
        
    def get_manifold_size(self) -> int:
        return len(self.manifold.keys())
