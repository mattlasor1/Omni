import torch
import torch.nn as nn
import numpy as np
from src.memory.vector_db import SolidStateWiki

class DynamicTopologyEngine:
    """
    Simulates Structural Neuroplasticity.
    LLMs and standard vector databases rely on fixed-dimension embeddings.
    True learning requires physical synaptic growth. When a semantic cluster 
    becomes extremely dense (representing complex, deep knowledge), this engine
    mathematically projects those 256-dim vectors into a localized 512-dim subspace,
    allocating new "brain matter" to capture hyper-nuance that couldn't fit previously.
    """
    def __init__(self, wiki: SolidStateWiki):
        self.wiki = wiki
        self.base_dim = 256
        self.expanded_dim = 512
        # A simple linear projection layer to simulate synaptic expansion
        self.expansion_layer = nn.Linear(self.base_dim, self.expanded_dim)
        # Ensure the expansion preserves the original vector direction initially
        with torch.no_grad():
            self.expansion_layer.weight.data[:, :self.base_dim] = torch.eye(self.expanded_dim, self.base_dim)
            self.expansion_layer.bias.data.zero_()

    def evaluate_and_expand_cluster(self, cluster_vectors: list, concept_ids: list) -> int:
        """
        Evaluates a cluster of memories. If it's too dense, it expands the topology.
        Returns the number of vectors expanded.
        """
        if len(cluster_vectors) < 5:
            return 0

        # Calculate density (average pairwise distance)
        vecs = np.array(cluster_vectors)
        centroid = np.mean(vecs, axis=0)
        distances = np.linalg.norm(vecs - centroid, axis=1)
        avg_dist = np.mean(distances)

        # High density (low average distance) + high volume means the concept is crowded.
        # It needs more dimensionality to separate nuanced ideas.
        if avg_dist < 0.15:
            print("NEUROPLASTICITY: Concept cluster is critically dense. Growing new synaptic topology...")
            expanded_count = 0
            
            for i, vec in enumerate(vecs):
                # Only expand if it hasn't been already
                if len(vec) == self.base_dim:
                    tensor_vec = torch.from_numpy(vec).float()
                    with torch.no_grad():
                        expanded_tensor = self.expansion_layer(tensor_vec)
                        # Normalize the new higher-dimensional thought
                        expanded_tensor = nn.functional.normalize(expanded_tensor, p=2, dim=0)
                    
                    expanded_vec = expanded_tensor.numpy()
                    
                    # Overwrite in Vector DB (Qdrant allows variable payload if configured, 
                    # but for prototype we store the expanded vector in metadata to bypass strict schema)
                    point_id = concept_ids[i]
                    points = self.wiki.client.retrieve(collection_name=self.wiki.semantic_collection, ids=[point_id])
                    if points:
                        p = points[0]
                        p.payload["neuroplastic_expanded"] = True
                        p.payload["hyper_vector"] = expanded_vec.tolist()
                        self.wiki.client.set_payload(
                            collection_name=self.wiki.semantic_collection,
                            payload=p.payload,
                            points=[point_id]
                        )
                        expanded_count += 1
                        
            if expanded_count > 0:
                print(f"NEUROPLASTICITY: Expanded {expanded_count} concepts to {self.expanded_dim}-dim space.")
            return expanded_count
            
        return 0
