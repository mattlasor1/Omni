from src.learning.reasoning import CognitiveReasoningEngine
from src.memory.vector_db import SolidStateWiki

class DualProcessRouter:
    """
    Implements Kahneman's System 1 and System 2 thinking.
    If a query maps to a highly confident, deeply embedded memory, the twin 
    responds instantly using heuristics (System 1). 
    If the query is novel or complex, it invokes slow, deliberate LLM reasoning (System 2).
    """
    def __init__(self, wiki: SolidStateWiki, reasoning: CognitiveReasoningEngine):
        self.wiki = wiki
        self.reasoning = reasoning

    def route_query(self, query: str, context_points: list, tom_instruction: str) -> tuple[str, str]:
        """
        Returns a tuple: (Generated Response, Process Used ("System 1" or "System 2"))
        """
        if not context_points:
            return self._run_system_2(query, [], tom_instruction), "System 2"

        # Evaluate familiarity/confidence
        best_point = context_points[0]
        alpha = best_point.payload.get("bayes_alpha", 1.0)
        beta = best_point.payload.get("bayes_beta", 1.0)
        depth = best_point.payload.get("fractal_depth", 0)
        
        # Calculate belief
        belief = alpha / (alpha + beta)
        
        # Heuristic: If we are highly confident (>0.9) AND the memory is deep (>2), it's instinctual.
        # We can bypass the complex LLM prompt and return a fast, direct heuristic response.
        if belief > 0.9 and depth >= 2:
            return self._run_system_1(query, best_point), "System 1"
        else:
            return self._run_system_2(query, context_points, tom_instruction), "System 2"

    def _run_system_1(self, query: str, point) -> str:
        """Fast, instinctual heuristic response based purely on the vector memory."""
        concept = point.payload.get("concept", "")
        return f"[System 1 Instinct]: {concept}"

    def _run_system_2(self, query: str, context_points: list, tom_instruction: str) -> str:
        """Slow, deliberate LLM reasoning."""
        if not self.reasoning.client:
            return "Cognitive LLM offline."
            
        context_strings = [p.payload.get("concept", "") for p in context_points]
        context_block = "\n".join([f"- {c}" for c in context_strings])
        
        prompt = (
            f"Query: {query}\n\n"
            f"Relevant Knowledge:\n{context_block}\n\n"
            f"Generate a thoughtful response based ONLY on the provided memories."
        )

        try:
            return self.reasoning._generate_generic(
                system_prompt=f"You are a digital twin responding to a user. {tom_instruction}",
                user_prompt=prompt,
                max_tokens=300,
                temperature=0.7
            )
        except Exception as e:
            return f"System 2 Error: {e}"
