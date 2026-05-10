from src.memory.graph_db import CausalGraphMemory
from src.learning.reasoning import CognitiveReasoningEngine

class TheoryOfMindEngine:
    """
    Allows the twin to model the epistemic state of the User or other Agents.
    Instead of assuming the user knows what the twin knows, the twin tracks
    what concepts it has explained to the user.
    """
    def __init__(self, graph: CausalGraphMemory, reasoning: CognitiveReasoningEngine):
        self.graph = graph
        self.reasoning = reasoning

    def model_audience(self, user_id: str, query: str, retrieved_concepts: list) -> str:
        """
        Adjusts the system prompt based on what the twin believes the user knows.
        """
        # In a full system, we would query the graph for edges between 'user_id' and 'concept_id'.
        # For the prototype, we use the LLM to deduce the user's intent/knowledge gap from the query.
        
        if not self.reasoning.client:
            return "You are a helpful AI."

        concept_strings = [p.payload.get("concept", "") for p in retrieved_concepts]
        knowledge_base = "\n".join([f"- {c}" for c in concept_strings])

        prompt = (
            f"A user ({user_id}) asked: '{query}'\n\n"
            f"Your knowledge base contains:\n{knowledge_base}\n\n"
            "Analyze the user's question. What do they likely already know? What are they confused about? "
            "Write a 2-sentence instructional prompt that tells the generation LLM exactly how to tone "
            "and tailor its response so it doesn't talk down to the user or assume they know too much."
        )

        try:
            tom_instruction = self.reasoning._generate_generic(
                system_prompt="You model user knowledge based on interaction history.",
                user_prompt=prompt,
                max_tokens=100,
                temperature=0.3
            )
            print(f"THEORY OF MIND: {tom_instruction}")
            return tom_instruction
        except Exception:
            return "Answer clearly and respectfully."

    def log_interaction(self, user_id: str, concept_ids: list[str]):
        """
        Records that the user has been exposed to these concepts, 
        mapping them in the causal graph.
        """
        self.graph.add_event(user_id, {"type": "user_agent"})
        for cid in concept_ids:
            # The user was exposed to this concept
            self.graph.link_causal(cid, user_id, confidence=0.8)
