import time
from src.memory.vector_db import SolidStateWiki
from src.memory.graph_db import CausalGraphMemory
from src.learning.epistemology import BayesianEngine

class SynapticEntropyEngine:
    """
    The Art of Forgetting.
    To maintain cognitive elasticity and sanity, a mind must degrade unused memories.
    This engine loops over the semantic and episodic memory stores, applying a
    mathematical decay to the Bayesian confidence of all concepts. If a concept's
    confidence decays to near-zero and has few causal links, it is permanently pruned.
    """
    def __init__(self, wiki: SolidStateWiki, graph: CausalGraphMemory, bayes: BayesianEngine):
        self.wiki = wiki
        self.graph = graph
        self.bayes = bayes
        self.decay_rate = 0.05 # Rate of negative evidence applied during sleep

    def prune_memories(self) -> dict:
        """
        Executes a decay and prune cycle. Usually run during 'Sleep' phases.
        """
        print("ENTROPY: Initiating Synaptic Pruning...")
        stats = {"decayed": 0, "pruned": 0}
        try:
            # 1. Scroll through semantic memory
            res = self.wiki.client.scroll(
                collection_name=self.wiki.semantic_collection,
                limit=1000,
                with_payload=True
            )[0]

            ids_to_delete = []

            for point in res:
                # 2. Skip Archetypes (Immutable truths)
                if point.payload.get("archetype", False):
                    continue

                alpha = point.payload.get("bayes_alpha", 1.0)
                beta = point.payload.get("bayes_beta", 1.0)

                # 3. Apply entropy (increase negative evidence slightly)
                _, new_beta = self.bayes.bayesian_update(alpha, beta, 0.0, self.decay_rate)
                
                # Calculate new belief
                belief = self.bayes.calculate_belief(alpha, new_beta)
                
                # Check causal gravity (is this a foundational concept?)
                causal_edges = len(list(self.graph.graph.edges(point.id))) if self.graph.graph.has_node(point.id) else 0

                # 4. Pruning threshold: Very low belief + no causal importance
                if belief < 0.2 and causal_edges < 2:
                    ids_to_delete.append(point.id)
                else:
                    # Save decayed state
                    point.payload["bayes_beta"] = new_beta
                    self.wiki.client.set_payload(
                        collection_name=self.wiki.semantic_collection,
                        payload=point.payload,
                        points=[point.id]
                    )
                    stats["decayed"] += 1

            # 5. Delete pruned memories entirely
            if ids_to_delete:
                self.wiki.client.delete(
                    collection_name=self.wiki.semantic_collection,
                    points_selector=ids_to_delete
                )
                
                # Remove from Causal Graph to prevent ghost links
                for pid in ids_to_delete:
                    if self.graph.graph.has_node(pid):
                        self.graph.graph.remove_node(pid)
                self.graph.save_graph()
                
                stats["pruned"] += len(ids_to_delete)
                print(f"ENTROPY: Pruned {len(ids_to_delete)} decayed concepts into the void.")

            return stats
        except Exception as e:
            print(f"ENTROPY Engine Failed: {e}")
            return stats
