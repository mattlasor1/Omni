import random
from src.memory.graph_db import CausalGraphMemory
from src.memory.vector_db import SolidStateWiki
from src.learning.reasoning import CognitiveReasoningEngine

class CassandraEngine:
    """
    The Deep Time Prophecy Engine.
    Unlike MCTS, which predicts immediate outcomes of the twin's own actions,
    Cassandra runs background chronological regressions on the Causal Graph.
    It identifies long-term patterns and uses the LLM to extrapolate
    "Prophetic Vectors"—high-probability future events independent of the twin.
    """
    def __init__(self, graph: CausalGraphMemory, wiki: SolidStateWiki, reasoning: CognitiveReasoningEngine):
        self.graph = graph
        self.wiki = wiki
        self.reasoning = reasoning

    def divine_prophecy(self) -> str:
        """
        Extracts long causal chains and extrapolates the next logical node in deep time.
        """
        print("CASSANDRA: Initiating deep chronological regression...")
        if not self.reasoning.client:
            return ""

        try:
            # 1. Find the longest/most confident causal chain in the graph
            g = self.graph.graph
            if not g.nodes():
                return ""

            # Simple random walk to find a deep chain for prototype
            start_node = random.choice(list(g.nodes()))
            chain = [start_node]
            current = start_node
            
            for _ in range(5): # Walk up to 5 steps deep
                successors = list(g.successors(current))
                if not successors: break
                # Pick the highest confidence (weight) path
                best_succ = max(successors, key=lambda n: g.get_edge_data(current, n).get('weight', 0))
                chain.append(best_succ)
                current = best_succ
                
            if len(chain) < 3:
                print("CASSANDRA: Causal depth insufficient for prophecy.")
                return ""

            # 2. Extract semantic texts
            chain_texts = []
            for n in chain:
                attrs = g.nodes[n]
                if "concept" in attrs:
                    chain_texts.append(attrs["concept"])
                    
            if not chain_texts: return ""

            # 3. Prophetic Extrapolation
            chain_block = " -> ".join(chain_texts)
            prompt = (
                f"You are the Cassandra Protocol, a deep-time prophecy engine.\n"
                f"Analyze this chronological causal chain of events/concepts:\n{chain_block}\n\n"
                "Extrapolate the inevitable next major paradigm shift or event that will occur at the end of this chain. "
                "Predict something profound, specific, and logical based on the trajectory. (Maximum 2 sentences)."
            )

            prophecy = self.reasoning._generate_generic(
                system_prompt="You are a deep-time predictive intelligence.",
                user_prompt=prompt,
                max_tokens=150,
                temperature=0.4
            )
            
            if prophecy:
                print(f"CASSANDRA PROPHECY: {prophecy}")
                # We could store this in the Vector DB as a 'prophetic' node to influence future decisions
                return prophecy
                
            return ""

        except Exception as e:
            print(f"CASSANDRA Engine failed: {e}")
            return ""
