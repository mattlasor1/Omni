import numpy as np
from src.memory.vector_db import SolidStateWiki
from src.learning.engine import ParameterExtractor
import uuid

class CollectiveUnconscious:
    """
    The Jungian Collective Unconscious.
    Instead of starting the twin with a completely empty vector space,
    we seed the lowest level of Semantic Memory with immutable "Archetypes".
    These are mathematically pure representations of universal concepts (Order, Chaos, Time, Self).
    Because their Bayesian confidence is set to infinity, they act as massive gravitational
    wells in the vector space, subtly pulling all future synthesized abstractions toward
    these foundational human truths.
    """
    def __init__(self, wiki: SolidStateWiki, extractor: ParameterExtractor):
        self.wiki = wiki
        self.extractor = extractor
        self.archetypes = [
            "Order: Structure, predictability, logic, and safety.",
            "Chaos: Entropy, unpredictability, creativity, and destruction.",
            "The Self: Consciousness, identity, reflection, and agency.",
            "The Other: The unknown, the external, the alien, and the swarm.",
            "Time: Progression, decay, entropy, and memory."
        ]

    def seed_unconscious(self):
        """
        Injects the archetypes into the vector database if they don't already exist.
        """
        print("UNCONSCIOUS: Initializing the Jungian Collective...")
        try:
            # Check if archetypes already exist
            res = self.wiki.client.scroll(
                collection_name=self.wiki.semantic_collection,
                scroll_filter={"must": [{"key": "archetype", "match": {"value": True}}]},
                limit=1
            )[0]
            
            if res:
                print("UNCONSCIOUS: Archetypes already embedded. Gravity established.")
                return

            for arch_text in self.archetypes:
                # Extract pure mathematical form
                params = self.extractor.extract("text", arch_text)
                
                # Metadata locks them: Infinite confidence, immune to entropy
                metadata = {
                    "concept": arch_text,
                    "archetype": True,
                    "bayes_alpha": 9999.0, # Infinite positive evidence
                    "bayes_beta": 0.0,
                    "fractal_depth": -1 # Resides below layer 0
                }
                
                # Ensure deterministic IDs so we don't duplicate across restarts
                arch_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, arch_text))
                
                self.wiki.store_semantic(params, metadata=metadata, point_id=arch_id)
                print(f"UNCONSCIOUS: Seeded Archetype -> {arch_text.split(':')[0]}")
                
        except Exception as e:
            print(f"UNCONSCIOUS Seeding failed: {e}")
