import networkx as nx
import os
import json
from typing import Dict, Any, List

class CausalGraphMemory:
    """
    Maintains a Causal and Temporal Knowledge Graph.
    While Vector databases handle 'similarity' and 'semantic nearness',
    this graph explicitly tracks chronological sequences and causal links
    ("Event A caused Concept B" or "Observation X followed Observation Y").
    This bridges a crucial gap in human-like learning: Causality.
    """
    def __init__(self, storage_path: str = "data/causal_graph.json"):
        self.storage_path = storage_path
        self.graph = nx.DiGraph()
        self._load_graph()

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

    def _load_graph(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.graph = nx.node_link_graph(data)
            except Exception as e:
                print(f"Failed to load graph: {e}. Starting fresh.")

    def save_graph(self):
        self._ensure_dir()
        try:
            data = nx.node_link_data(self.graph)
            with open(self.storage_path, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Failed to save graph: {e}")

    def add_event(self, node_id: str, attributes: Dict[str, Any]):
        """
        Adds a single temporal/episodic event or semantic concept to the graph.
        """
        self.graph.add_node(node_id, **attributes)
        self.save_graph()

    def link_temporal(self, source_id: str, target_id: str):
        """
        Explicitly links two events chronologically (Source happened before Target).
        """
        if self.graph.has_node(source_id) and self.graph.has_node(target_id):
            self.graph.add_edge(source_id, target_id, relation="temporal", weight=1.0)
            self.save_graph()

    def link_causal(self, cause_id: str, effect_id: str, confidence: float = 1.0):
        """
        Explicitly links a cause to an effect, e.g., an episodic cluster 
        forming a semantic concept.
        """
        if self.graph.has_node(cause_id) and self.graph.has_node(effect_id):
            self.graph.add_edge(cause_id, effect_id, relation="causal", weight=confidence)
            self.save_graph()

    def get_causal_chain(self, node_id: str, depth: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves the causal history (why something happened) or future 
        (what it caused) for a specific memory.
        """
        if not self.graph.has_node(node_id):
            return []
            
        chain = []
        # Predecessors (Causes)
        for pred in self.graph.predecessors(node_id):
            edge_data = self.graph.get_edge_data(pred, node_id)
            if edge_data.get("relation") == "causal":
                chain.append({"type": "cause", "node": pred, "attributes": self.graph.nodes[pred]})
                
        # Successors (Effects)
        for succ in self.graph.successors(node_id):
            edge_data = self.graph.get_edge_data(node_id, succ)
            if edge_data.get("relation") == "causal":
                chain.append({"type": "effect", "node": succ, "attributes": self.graph.nodes[succ]})
                
        return chain
