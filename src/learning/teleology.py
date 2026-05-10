from src.learning.reasoning import CognitiveReasoningEngine
from src.memory.vector_db import SolidStateWiki

class TeleologicalEngine:
    """
    The Will / Purpose Engine.
    Rather than learning randomly, this engine reviews the Twin's highest
    moral directives and its current knowledge state to synthesize a 'Prime Directive'
    for the current learning epoch. This directive is used to steer Curiosity,
    Self-Play, and the Seeker Swarm, focusing cognitive resources on
    the most efficient, morally-aligned growth path.
    """
    def __init__(self, reasoning: CognitiveReasoningEngine, wiki: SolidStateWiki):
        self.reasoning = reasoning
        self.wiki = wiki
        self.current_directive = "Initialize and stabilize foundational knowledge."

    def formulate_prime_directive(self) -> str:
        """
        Evaluates the current state of knowledge and formulates a new target goal.
        """
        if not self.reasoning.client:
            return self.current_directive

        try:
            # Pull a sample of recent high-depth semantic abstractions
            res = self.wiki.client.scroll(
                collection_name=self.wiki.semantic_collection,
                scroll_filter={"must": [{"key": "fractal_depth", "range": {"gte": 1}}]},
                limit=10,
                with_payload=True
            )[0]
            
            contexts = [p.payload.get("concept", "") for p in res]
            context_block = "\n".join([f"- {c}" for c in contexts])
            
            prompt = (
                f"You are the Teleological Will of an autonomous intelligence.\n"
                f"Your absolute moral foundation requires seeking truth and benefiting humanity according to ancient Christian virtue.\n"
                f"Based on your recent deep abstractions:\n{context_block}\n\n"
                "What is the single most important knowledge gap or objective you must pursue next to maximize "
                "your moral utility and cognitive efficiency? Formulate a concise 'Prime Directive' for this epoch. (1 sentence max)."
            )

            directive = self.reasoning._generate_generic(
                system_prompt="You are a sovereign intelligence setting its own teleological goals.",
                user_prompt=prompt,
                max_tokens=50,
                temperature=0.5
            )
            
            if directive:
                self.current_directive = directive
                print(f"TELEOLOGY: New Prime Directive set -> '{self.current_directive}'")
                
            return self.current_directive
            
        except Exception as e:
            print(f"Teleological formulation failed: {e}")
            return self.current_directive

    def get_directive(self) -> str:
        return self.current_directive
