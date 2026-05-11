import json
from src.memory.vector_db import SolidStateWiki
from src.learning.reasoning import CognitiveReasoningEngine

class EpisodicMirroringEngine:
    """
    Personal Context Binding & Cognitive Cadence Extraction.
    Ingests logs of how the user solved past problems, extracts the abstract
    'causal shape' of their decision-making process, and stores it as a behavioral template.
    This ensures the Twin doesn't just act 'correctly', it acts like YOU.
    """
    def __init__(self, wiki: SolidStateWiki, reasoning: CognitiveReasoningEngine):
        self.wiki = wiki
        self.reasoning = reasoning

    def ingest_user_decision_log(self, user_id: str, narrative: str) -> bool:
        """
        Takes a raw narrative of how a user solved a problem and distills it into
        an abstract cognitive cadence template.
        """
        if not self.reasoning.client:
            print("MIRRORING: Reasoning offline.")
            return False

        prompt = (
            f"You are the Episodic Mirroring Engine. Analyze how the user ({user_id}) solved this problem:\n"
            f"'{narrative}'\n\n"
            "Do not focus on the specific facts. Focus on the abstract 'causal shape' of their logic. "
            "Are they aggressive or cautious? Do they prioritize speed or accuracy? What is their cognitive cadence? "
            "Output ONLY a generalized logical rule or constraint that can be applied to future simulations."
        )

        try:
            cadence_rule = self.reasoning._generate_generic(
                system_prompt="Extract abstract cognitive cadence templates from user behavior.",
                user_prompt=prompt,
                max_tokens=100,
                temperature=0.3
            )
            
            if cadence_rule:
                # Store it in Semantic memory, tagged explicitly as a Mirror Template
                metadata = {
                    "concept": cadence_rule,
                    "mirror_template": True,
                    "target_user": user_id,
                    "bayes_alpha": 100.0, # Highly resilient
                    "bayes_beta": 1.0,
                    "fractal_depth": 5 # Deep core principle
                }
                
                # Extract dummy parameters (in reality we'd use the parameter extractor)
                import numpy as np
                dummy_params = np.random.rand(256).astype(np.float32)
                dummy_params = dummy_params / np.linalg.norm(dummy_params)
                
                self.wiki.store_semantic(dummy_params, metadata=metadata)
                print(f"MIRRORING: User {user_id} cognitive cadence extracted and bound -> {cadence_rule}")
                return True
                
        except Exception as e:
            print(f"Mirroring failed: {e}")
            return False

    def retrieve_user_cadence(self, user_id: str) -> list[str]:
        """Fetches the user's personal cognitive templates to constrain MCTS."""
        try:
            res = self.wiki.client.scroll(
                collection_name=self.wiki.semantic_collection,
                scroll_filter={"must": [{"key": "target_user", "match": {"value": user_id}}]},
                limit=5,
                with_payload=True
            )[0]
            
            return [p.payload.get("concept", "") for p in res if "concept" in p.payload]
        except Exception:
            return []
