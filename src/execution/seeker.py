import time
from typing import List
from src.memory.cache import LivestreamCache
from src.learning.reasoning import CognitiveReasoningEngine

class SeekerSwarm:
    """
    Active Context Fetching Swarm.
    When the Curiosity Engine asks a question, this module spawns lightweight
    simulated web-crawlers/API agents to fetch the answer and instantly flood
    the cache with the missing context.
    """
    def __init__(self, cache: LivestreamCache, reasoning: CognitiveReasoningEngine):
        self.cache = cache
        self.reasoning = reasoning

    def dispatch_seekers(self, query: str) -> bool:
        """
        Dispatches the swarm to find the answer to a specific curiosity query.
        """
        print(f"SEEKER SWARM: Dispatching agents to resolve knowledge gap: '{query}'")
        
        if not self.reasoning.client:
            print("SEEKER SWARM: External API offline.")
            return False

        # In a real environment, this would hit SerpAPI, Wikipedia, or scrape links.
        # Here, we use the LLM to 'simulate' retrieving an external document that answers the query.
        prompt = (
            f"You are an external search engine. Provide a highly detailed, factual, and context-rich "
            f"paragraph that definitively answers the following question: '{query}'"
        )
        
        try:
            response = self.reasoning.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=250,
                temperature=0.2
            )
            
            fetched_context = response.choices[0].message.content
            
            # Flood the cache with the retrieved context
            if self.cache:
                self.cache.add_to_stream({
                    "type": "text",
                    "source_id": "SEEKER_SWARM",
                    "content": fetched_context,
                    "context": {"seeker_resolution": True, "original_query": query}
                })
                print("SEEKER SWARM: Context successfully fetched and injected into cache.")
                
                # Increment metric
                self.cache.client.incr("omnitwin:metrics:seeker_dispatches")
                return True
                
        except Exception as e:
            print(f"SEEKER SWARM Failed: {e}")
            return False
