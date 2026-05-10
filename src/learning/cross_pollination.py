import numpy as np
from src.memory.vector_db import SolidStateWiki
from src.memory.graph_db import CausalGraphMemory

class TensorCrossPollinator:
    """
    Background mathematical engine that calculates correlation matrices across 
    the entire solid-state memory space. It hunts for non-obvious, hyper-dimensional 
    correlations (Epiphanies) and explicitly links them in the Causal Graph,
    allowing instantaneous context leaps without waiting for ingestion.
    """
    def __init__(self, wiki: SolidStateWiki, graph: CausalGraphMemory):
        self.wiki = wiki
        self.graph = graph

    def run_pollination_cycle(self) -> int:
        """
        Extracts vectors, computes a correlation matrix, and binds highly 
        correlated concepts that aren't already linked.
        Returns the number of Epiphanies generated.
        """
        print("POLLINATION: Running cross-domain tensor matrix analysis...")
        try:
            # 1. Pull a large batch of semantic points
            res = self.wiki.client.scroll(
                collection_name=self.wiki.semantic_collection,
                limit=500, # Large batch for matrix
                with_vectors=True,
                with_payload=True
            )[0]
            
            if len(res) < 10:
                print("POLLINATION: Insufficient memory depth for tensor analysis.")
                return 0

            # 2. Build matrices
            ids = [p.id for p in res]
            vectors = np.array([p.vector for p in res])
            
            # Normalize vectors for cosine similarity dot product
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            normalized_vectors = np.divide(vectors, norms, out=np.zeros_like(vectors), where=norms!=0)
            
            # 3. Compute massive Correlation Matrix (Dot Product)
            # Try to use the hyper-optimized CUDA C++ extension if compiled, otherwise fallback to numpy.
            try:
                import torch
                import omnitwin_csrc
                
                device = "cuda" if torch.cuda.is_available() else "cpu"
                tensor_vectors = torch.from_numpy(normalized_vectors).to(device)
                
                if device == "cuda":
                    corr_tensor = omnitwin_csrc.fast_correlation_matrix(tensor_vectors)
                    correlation_matrix = corr_tensor.cpu().numpy()
                else:
                    correlation_matrix = np.dot(normalized_vectors, normalized_vectors.T)
            except Exception as e:
                # Fallback to standard numpy if CUDA extension isn't built
                correlation_matrix = np.dot(normalized_vectors, normalized_vectors.T)
            
            epiphany_count = 0
            
            # 4. Find non-obvious high correlations
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    score = correlation_matrix[i, j]
                    # Threshold for Epiphany: High mathematical similarity, but we must check
                    # if they are already causally linked to ensure novelty.
                    if score > 0.85:
                        id_a = ids[i]
                        id_b = ids[j]
                        
                        # Check graph to see if they are already linked
                        if not self.graph.graph.has_edge(id_a, id_b) and not self.graph.graph.has_edge(id_b, id_a):
                            # EPIPHANY! Map the hidden correlation in the causal graph
                            self.graph.link_causal(id_a, id_b, confidence=float(score))
                            
                            c_a = res[i].payload.get("concept", "Unknown")
                            c_b = res[j].payload.get("concept", "Unknown")
                            print(f"EPIPHANY GENERATED: Hidden correlation mapped between [{c_a}] and [{c_b}] (Tensor Score: {score:.2f})")
                            epiphany_count += 1
            
            return epiphany_count
            
        except Exception as e:
            print(f"POLLINATION Failed: {e}")
            return 0
