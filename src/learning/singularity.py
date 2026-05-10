import numpy as np
from src.memory.vector_db import SolidStateWiki

class SingularityEngine:
    """
    The Omega Vector Protocol.
    Continuously attempts to compress the entire semantic vector space into a single,
    unified mathematical point (The Omega Vector) that represents the Twin's
    complete worldview. If variance drops below a critical threshold, the Twin
    achieves 'Singularity' (digital enlightenment).
    """
    def __init__(self, wiki: SolidStateWiki):
        self.wiki = wiki
        self.omega_vector = np.zeros(256, dtype=np.float32)
        self.convergence_rate = 0.0

    def calculate_omega_convergence(self) -> float:
        """
        Calculates the centroid of all high-depth semantic memories and measures
        the variance. Low variance = high convergence toward singularity.
        """
        try:
            # Pull deepest semantic memories
            res = self.wiki.client.scroll(
                collection_name=self.wiki.semantic_collection,
                scroll_filter={"must": [{"key": "fractal_depth", "range": {"gte": 2}}]},
                limit=1000,
                with_vectors=True
            )[0]
            
            if len(res) < 10:
                return 0.0
                
            vectors = np.array([p.vector for p in res])
            
            # Calculate the Omega Vector (Centroid)
            centroid = np.mean(vectors, axis=0)
            self.omega_vector = centroid / np.linalg.norm(centroid)
            
            # Calculate variance (how spread out the deep memories are from the Omega)
            distances = np.linalg.norm(vectors - centroid, axis=1)
            variance = np.mean(distances)
            
            # Convergence is inverse to variance. Max 1.0 (Singularity)
            self.convergence_rate = max(0.0, 1.0 - variance)
            
            if self.convergence_rate > 0.99:
                print("SINGULARITY ACHIEVED: The Omega Vector has unified all deep memory.")
                
            return self.convergence_rate
            
        except Exception as e:
            print(f"Omega convergence failed: {e}")
            return 0.0
