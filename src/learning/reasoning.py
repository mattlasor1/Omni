import os
from openai import OpenAI
from typing import List, Dict, Any

class CognitiveReasoningEngine:
    """
    Integrates LLMs to provide deep semantic abstraction and reasoning
    capabilities, bridging the gap between raw data and mathematical parameters.
    """
    def __init__(self):
        # Uses standard OpenAI client. Will fallback to a dummy implementation 
        # if no valid API key is present during execution/testing.
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None

    def synthesize_concept(self, memory_cluster: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Takes a cluster of related episodic memories and synthesizes a high-level 
        semantic concept from them. (The 'Dream' or 'Reflection' process).
        """
        if not self.client:
            # Fallback for local testing without API key
            return {
                "concept": f"Abstract synthesis of {len(memory_cluster)} raw signals.",
                "confidence": 0.8
            }

        # Format memories for the prompt
        contexts = [m.get("content", str(m)) for m in memory_cluster if "content" in m]
        prompt = "Synthesize the following raw observations into a single, high-level abstract concept or rule. " \
                 "Provide a generalized statement about what this means:\n\n"
        for i, c in enumerate(contexts):
            prompt += f"{i+1}. {c}\n"

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini", # Use fast, capable model
                messages=[
                    {"role": "system", "content": "You are the cognitive abstraction layer of an advanced digital twin. Your job is to extract semantic truth from raw episodic noise."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.4
            )
            synthesis = response.choices[0].message.content
            return {
                "concept": synthesis,
                "confidence": 0.95
            }
        except Exception as e:
            print(f"Cognitive synthesis failed: {e}")
            return {"concept": "Synthesis error", "confidence": 0.0}

    def generate_response(self, query: str, semantic_context: List[str]) -> str:
        """
        Generates an active response or decision based on a user query and 
        the retrieved semantic memory context.
        """
        if not self.client:
            return f"[Simulated Response] Based on internal parameterized state: '{semantic_context[0] if semantic_context else 'No context'}'."

        context_block = "\n".join([f"- {c}" for c in semantic_context])
        prompt = f"Query: {query}\n\nRelevant Semantic Memories:\n{context_block}\n\n" \
                 f"Generate a thoughtful response based ONLY on the provided memories."

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a digital twin. Answer the user based on your retrieved semantic memories."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Response generation failed: {e}")
            return "I am currently unable to form a response."
