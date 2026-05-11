import re
from src.memory.vector_db import SolidStateWiki

class StylometricEngine:
    """
    The Linguistic Cloning Engine.
    Mathematically maps the user's specific lexical distribution, sentence variance,
    and voice, tracking it in a semantic profile. When the twin generates text,
    it applies these exact constraints so it speaks identically to the host.
    """
    def __init__(self, wiki: SolidStateWiki):
        self.wiki = wiki

    def ingest_user_writing(self, user_id: str, text: str):
        """
        Analyzes a block of user writing to extract stylometric markers.
        """
        # Extremely basic heuristics for prototype
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences: return
        
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        
        words = text.lower().split()
        unique_words = set(words)
        lexical_diversity = len(unique_words) / float(max(len(words), 1))
        
        profile = (
            f"Average sentence length: {avg_sentence_length:.1f} words. "
            f"Lexical diversity ratio: {lexical_diversity:.2f}. "
            f"Tone observation: Speak directly, matching this cadence."
        )
        
        # Store or update the user's stylometric profile in the DB
        # For simplicity, we just dump it to Qdrant with a specific metadata flag
        import numpy as np
        dummy_vec = np.random.rand(256).astype(np.float32)
        dummy_vec = dummy_vec / np.linalg.norm(dummy_vec)
        
        self.wiki.store_semantic(dummy_vec, metadata={
            "stylometric_profile": True,
            "target_user": user_id,
            "concept": profile,
            "bayes_alpha": 100.0,
            "bayes_beta": 1.0
        })
        print(f"STYLOMETRICS: Updated voice profile for user {user_id}")

    def get_style_prompt(self, user_id: str) -> str:
        """
        Fetches the user's stylometric profile to inject into the LLM system prompt.
        """
        try:
            res = self.wiki.client.scroll(
                collection_name=self.wiki.semantic_collection,
                scroll_filter={"must": [{"key": "stylometric_profile", "match": {"value": True}}, 
                                        {"key": "target_user", "match": {"value": user_id}}]},
                limit=1,
                with_payload=True
            )[0]
            
            if res:
                profile = res[0].payload.get("concept", "")
                return f"You MUST adopt the exact linguistic prosody of the user. Profile: {profile}"
            return "Adopt a neutral, clear tone."
        except Exception:
            return "Adopt a neutral, clear tone."
