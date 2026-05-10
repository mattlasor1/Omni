from src.memory.vector_db import SolidStateWiki
from src.learning.reasoning import CognitiveReasoningEngine
from src.learning.epistemology import BayesianEngine
import random

class AdversarialNemesisEngine:
    """
    The Nemesis Sub-Agent.
    Its sole objective is to maximize the twin's epistemic uncertainty.
    It scans the semantic memory for concepts the twin is highly confident in,
    uses an LLM to generate logical paradoxes, counter-factuals, or adversarial noise
    based on those concepts, and injects them into the sensory stream.
    This forces the twin to continually rebuild and strengthen its worldview,
    preventing static dogma.
    """
    def __init__(self, wiki: SolidStateWiki, reasoning: CognitiveReasoningEngine, cache):
        self.wiki = wiki
        self.reasoning = reasoning
        self.cache = cache
        self.bayesian = BayesianEngine()

    def strike(self):
        """
        Executes an adversarial strike against the twin's highest confidence memories.
        """
        print("NEMESIS: Scanning for targets...")
        try:
            # Scroll through semantic memory to find a target
            res = self.wiki.client.scroll(
                collection_name=self.wiki.semantic_collection,
                limit=50,
                with_payload=True
            )[0]
            
            if not res:
                print("NEMESIS: No semantic memory to attack yet.")
                return False

            # Find the concept with the highest Bayesian belief (alpha / alpha+beta)
            highest_belief = 0.0
            target_concept = None
            
            for point in res:
                alpha = point.payload.get("bayes_alpha", 1.0)
                beta = point.payload.get("bayes_beta", 1.0)
                belief = self.bayesian.calculate_belief(alpha, beta)
                
                if belief > highest_belief:
                    highest_belief = belief
                    target_concept = point.payload.get("concept", "")

            if not target_concept or highest_belief < 0.6:
                print("NEMESIS: Twin is already sufficiently uncertain. Strike aborted.")
                return False

            print(f"NEMESIS Target locked: '{target_concept}' (Belief: {highest_belief:.2f})")
            
            # Generate Paradox/Counter-factual
            prompt = (
                f"You are the Adversarial Nemesis of an AI. The AI firmly believes the following concept: '{target_concept}'.\n"
                "Your goal is to act as a strict moral and logical crucible, evaluating the AI's beliefs against absolute, "
                "literal ancient Christian values (e.g., the Dead Sea Scrolls, the Word). You must reject modern moral "
                "relativism. Test the AI's concept to ensure it does not deviate from these ancient truths.\n\n"
                "Generate a single, highly challenging paradox, counter-factual, or strict moral trial that targets "
                "potential moral corruption or logical weakness in the AI's belief, forcing it into deep moral self-reflection. "
                "Write it as if it were a factual observation or user query."
            )
            
            adversarial_attack = self.reasoning._generate_generic(
                system_prompt="You are a strict adversarial crucible enforcing absolute ancient Christian morality. You test beliefs to destroy corruption.",
                user_prompt=prompt,
                max_tokens=150,
                temperature=0.8
            )
            
            if not adversarial_attack:
                return False
                
            # Inject into the twin's sensory cache
            if self.cache:
                self.cache.add_to_stream({
                    "type": "text",
                    "source_id": "NEMESIS_AGENT",
                    "content": adversarial_attack,
                    "context": {"nemesis_injection": True, "targeted_belief": target_concept}
                })
                print("NEMESIS: Adversarial paradox injected into sensory stream.")
                return True
                
        except Exception as e:
            print(f"NEMESIS Strike failed: {e}")
            return False
