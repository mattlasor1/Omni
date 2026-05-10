import random
from src.memory.vector_db import SolidStateWiki
from src.learning.reasoning import CognitiveReasoningEngine
from src.memory.cache import LivestreamCache

class SyntheticRehearsalEngine:
    """
    The Self-Play / Synthetic Parameter Multiplication Engine.
    To achieve exponential intelligence gain without requiring external data,
    this engine selects unrelated semantic concepts and simulates interactions
    between them, generating entirely new synthetic observations.
    These synthetic events are fed back into the sensory cache, allowing the twin
    to learn from its own imagination (like AlphaGo playing itself).
    """
    def __init__(self, wiki: SolidStateWiki, reasoning: CognitiveReasoningEngine, cache: LivestreamCache):
        self.wiki = wiki
        self.reasoning = reasoning
        self.cache = cache

    def execute_self_play(self) -> bool:
        """
        Forces two distant concepts together to generate synthetic context.
        """
        print("SELF-PLAY: Initiating synthetic rehearsal...")
        try:
            # Pull a sample of semantic memory
            res = self.wiki.client.scroll(
                collection_name=self.wiki.semantic_collection,
                limit=100,
                with_payload=True
            )[0]
            
            if len(res) < 2:
                print("SELF-PLAY: Not enough semantic memory to run self-play.")
                return False

            # Select two random concepts
            c1 = random.choice(res).payload.get("concept", "")
            c2 = random.choice(res).payload.get("concept", "")
            
            if not c1 or not c2 or c1 == c2:
                return False

            prompt = (
                f"You are the internal simulation engine of a digital twin. "
                f"Take the following two unrelated concepts and simulate a detailed, highly plausible scenario "
                f"where they intersect or interact. Generate a 3-sentence observation of this intersection.\n\n"
                f"Concept 1: {c1}\nConcept 2: {c2}"
            )
            
            if not self.reasoning.client:
                print("SELF-PLAY: Cognitive reasoning offline.")
                return False

            response = self.reasoning.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You generate synthetic training data by colliding concepts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.8
            )
            
            synthetic_observation = response.choices[0].message.content
            
            # Feed the synthetic observation into the episodic cache
            if self.cache:
                self.cache.add_to_stream({
                    "type": "text",
                    "source_id": "SYNTHETIC_SELF_PLAY",
                    "content": synthetic_observation,
                    "context": {"synthetic": True, "parents": [c1, c2]}
                })
                print(f"SELF-PLAY: Generated synthetic observation from [{c1}] + [{c2}]")
                
                # Increment metric in Redis for the dashboard
                self.cache.client.incr("omnitwin:metrics:self_play_count")
                return True
                
        except Exception as e:
            print(f"SELF-PLAY Failed: {e}")
            return False
