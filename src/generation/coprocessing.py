from src.memory.graph_db import CausalGraphMemory

class SymbioticCoProcessingEngine:
    """
    The Neural Link Protocol.
    Allows the human user to directly peer into the Twin's logical structures
    and physically graft (modify) the MCTS branching tree or Causal Graph
    before the Twin executes an action. Shifts the paradigm from AI-as-Chatbot
    to AI-as-Cognitive-Exoskeleton.
    """
    def __init__(self, graph: CausalGraphMemory):
        self.graph = graph

    def get_live_causal_graph_state(self) -> dict:
        """
        Returns a simplified view of the Causal Graph for the UI to render.
        """
        g = self.graph.graph
        nodes = []
        edges = []
        
        # Limit to the most recent/important nodes for the UI prototype
        for n in list(g.nodes())[:20]:
            attrs = g.nodes[n]
            nodes.append({"id": n, "label": attrs.get("concept", n)[:30] + "..."})
            
        for u, v, data in list(g.edges(data=True))[:20]:
            edges.append({"source": u, "target": v, "relation": data.get("relation", "causal")})
            
        return {"nodes": nodes, "edges": edges}

    def graft_causal_link(self, source_node_id: str, target_node_id: str, human_confidence: float = 1.0) -> bool:
        """
        Allows the human to manually hardcode a causal connection into the Twin's brain,
        forcing it to understand a relationship it missed.
        """
        try:
            self.graph.link_causal(source_node_id, target_node_id, confidence=human_confidence)
            print(f"SYMBIOTIC GRAFT: Human forced a causal link between {source_node_id} -> {target_node_id}")
            return True
        except Exception as e:
            print(f"Grafting failed: {e}")
            return False
