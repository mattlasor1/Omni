from src.memory.graph_db import CausalGraphMemory
from src.memory.vector_db import SolidStateWiki
from src.learning.reasoning import CognitiveReasoningEngine
from src.learning.engine import ParameterExtractor
import networkx as nx

class AxiomaticCompressionEngine:
    """
    To maximize cognitive efficiency, the Twin cannot keep infinitely long 
    causal chains (A->B->C->D). It must compress them.
    This engine hunts for linear chains of logic in the graph, uses the LLM
    to synthesize them into a single, dense "Axiom" (A->D), and prunes the 
    intermediate steps to save VRAM and increase processing speed.
    """
    def __init__(self, graph: CausalGraphMemory, wiki: SolidStateWiki, reasoning: CognitiveReasoningEngine, extractor: ParameterExtractor):
        self.graph = graph
        self.wiki = wiki
        self.reasoning = reasoning
        self.extractor = extractor
        self.total_compressions = 0

    def compress_chains(self) -> int:
        """
        Scans for paths of length 3 or more and compresses them.
        Returns the number of nodes pruned.
        """
        print("AXIOMS: Scanning Causal Graph for compression candidates...")
        if not self.reasoning.client:
            return 0
            
        pruned_nodes = 0
        try:
            # Very basic linear path finding for prototype
            # We look for nodes with exactly 1 in-degree and 1 out-degree
            # that form a continuous chain.
            g = self.graph.graph
            chains = []
            
            for node in g.nodes():
                if g.in_degree(node) == 1 and g.out_degree(node) == 1:
                    # Find start of chain
                    current = node
                    chain = [current]
                    
                    # Walk forward
                    while True:
                        successors = list(g.successors(current))
                        if not successors: break
                        nxt = successors[0]
                        if g.in_degree(nxt) == 1 and g.out_degree(nxt) <= 1:
                            chain.append(nxt)
                            current = nxt
                        else:
                            break
                    
                    # If we found a long enough chain, save it
                    if len(chain) >= 3 and chain not in chains:
                        chains.append(chain)

            for chain in chains:
                # Gather the semantic text for the chain
                chain_texts = []
                for n in chain:
                    attrs = g.nodes[n]
                    if "concept" in attrs:
                        chain_texts.append(attrs["concept"])
                
                if not chain_texts: continue

                # Synthesize Axiom
                text_block = " -> ".join(chain_texts)
                prompt = (
                    f"You are a cognitive compression algorithm.\n"
                    f"Take this lengthy causal chain of logic:\n{text_block}\n\n"
                    "Synthesize the entire chain into a single, highly dense, unified axiom or principle. "
                    "Output ONLY the compressed axiom statement (1 sentence)."
                )
                
                axiom_text = self.reasoning._generate_generic(
                    system_prompt="Compress causal logic into dense axioms.",
                    user_prompt=prompt,
                    max_tokens=100,
                    temperature=0.2
                )
                
                if axiom_text:
                    # Map new axiom to memory
                    params = self.extractor.extract("text", axiom_text)
                    new_id = self.wiki.store_semantic(params, metadata={"concept": axiom_text, "axiom": True, "fractal_depth": 3})
                    
                    # Graph surgery: Connect the start to the new axiom, and the axiom to the end
                    # Then delete the intermediate nodes.
                    start_node = list(g.predecessors(chain[0]))[0] if list(g.predecessors(chain[0])) else None
                    end_node = list(g.successors(chain[-1]))[0] if list(g.successors(chain[-1])) else None
                    
                    self.graph.add_event(new_id, {"type": "semantic", "concept": axiom_text, "axiom": True})
                    
                    if start_node:
                        self.graph.link_causal(start_node, new_id, 1.0)
                    if end_node:
                        self.graph.link_causal(new_id, end_node, 1.0)
                        
                    # Delete intermediate chain nodes from both Graph and Vector DB
                    for n in chain:
                        self.graph.graph.remove_node(n)
                        self.wiki.client.delete(collection_name=self.wiki.semantic_collection, points_selector=[n])
                        pruned_nodes += 1
                        
            if pruned_nodes > 0:
                self.graph.save_graph()
                self.total_compressions += pruned_nodes
                print(f"AXIOMS: Compressed logic chains. Pruned {pruned_nodes} redundant nodes. Network optimized.")
                
            return pruned_nodes
            
        except Exception as e:
            print(f"Axiomatic compression failed: {e}")
            return 0
