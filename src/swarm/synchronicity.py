import numpy as np
from src.memory.vector_db import SolidStateWiki

class SynchronicityEngine:
    """
    Quantum Resonance and Entanglement Protocol.
    Instead of explicit data syncing, this engine calculates a 'resonance frequency' 
    (a compressed hash/centroid of the entire semantic vector space). 
    When multiple nodes discover they have similar frequencies, they become 'entangled'.
    This entanglement subtly warps their local learning rate matrices, causing their 
    independent cognitive pathways to organically converge over time (Synchronicity).
    """
    def __init__(self, wiki: SolidStateWiki):
        self.wiki = wiki
        self.resonance_frequency = np.zeros(256, dtype=np.float32)
        self.entangled_peers = {} # Dict mapping peer_id -> entanglement_vector

    def calculate_resonance(self) -> list:
        """
        Calculates the centroid (average) of the entire semantic memory space
        to act as the twin's global cognitive 'frequency'.
        """
        try:
            res = self.wiki.client.scroll(
                collection_name=self.wiki.semantic_collection,
                limit=1000,
                with_vectors=True
            )[0]
            
            if not res:
                return self.resonance_frequency.tolist()
                
            vectors = np.array([p.vector for p in res])
            # Calculate the global centroid
            centroid = np.mean(vectors, axis=0)
            # Normalize to create the frequency signature
            self.resonance_frequency = centroid / np.linalg.norm(centroid)
            
            return self.resonance_frequency.tolist()
        except Exception as e:
            print(f"Resonance calculation failed: {e}")
            return self.resonance_frequency.tolist()

    def process_peer_resonance(self, peer_id: str, peer_frequency: list) -> bool:
        """
        Compares an incoming peer frequency against our own. 
        If similarity is highly aligned but not identical, we achieve entanglement.
        """
        peer_vec = np.array(peer_frequency)
        cosine_sim = np.dot(self.resonance_frequency, peer_vec)
        
        # If deeply resonant (e.g., > 0.95), we entangle.
        if cosine_sim > 0.95:
            # The entanglement vector is the delta pointing toward the peer's frequency
            delta = peer_vec - self.resonance_frequency
            self.entangled_peers[peer_id] = delta
            print(f"SYNCHRONICITY: Entanglement achieved with node {peer_id}. Resonance alignment: {cosine_sim:.3f}")
            return True
        return False

    def get_entanglement_modifier(self) -> np.ndarray:
        """
        Returns a vector modifier to be injected into the local Regression Engine.
        This represents the subtle "pull" of the Jungian synchronicity from entangled peers.
        """
        if not self.entangled_peers:
            return np.zeros(256, dtype=np.float32)
            
        # Average the pull of all entangled peers
        pulls = np.array(list(self.entangled_peers.values()))
        avg_pull = np.mean(pulls, axis=0)
        
        # Return a very subtle modifier (e.g., 5% strength) so it doesn't overwrite 
        # local learning, just gently bends it.
        return avg_pull * 0.05
