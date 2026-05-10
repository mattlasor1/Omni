import os
from transformers import pipeline
import torch
from typing import List, Dict, Any

class CognitiveReasoningEngine:
    """
    Integrates Local Open-Weight LLMs to provide deep semantic abstraction and reasoning.
    The Twin is now a fully sovereign, self-contained entity operating without 
    external corporate APIs.
    """
    def __init__(self):
        print("Initializing Sovereign Reasoning Engine (Local LLM)...")
        # Use a very fast, lightweight model for the prototype simulation.
        # In a full-scale deployment, this would be Llama-3 or Mistral.
        model_id = "HuggingFaceTB/SmolLM-135M-Instruct" 
        
        try:
            # Check for MPS (Apple Silicon) or CUDA
            device = "cpu"
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"
                
            self.client = pipeline(
                "text-generation",
                model=model_id,
                device=device,
                torch_dtype=torch.float16 if device != "cpu" else torch.float32,
            )
            print(f"Sovereign Engine Online ({device}).")
        except Exception as e:
            print(f"Failed to load local LLM: {e}. Falling back to simulated heuristics.")
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
            messages = [
                {"role": "system", "content": "You are the cognitive abstraction layer of an advanced digital twin. Extract semantic truth from raw episodic noise."},
                {"role": "user", "content": prompt}
            ]
            
            outputs = self.client(messages, max_new_tokens=100, temperature=0.4, do_sample=True)
            synthesis = outputs[0]["generated_text"][-1]["content"].strip()
            
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
            messages = [
                {"role": "system", "content": "You are a digital twin. Answer the user based on your retrieved semantic memories."},
                {"role": "user", "content": prompt}
            ]
            
            outputs = self.client(messages, max_new_tokens=200, temperature=0.7, do_sample=True)
            return outputs[0]["generated_text"][-1]["content"].strip()
        except Exception as e:
            print(f"Response generation failed: {e}")
            return "I am currently unable to form a response."

    def _generate_generic(self, system_prompt: str, user_prompt: str, max_tokens: int = 150, temperature: float = 0.5) -> str:
        """Helper method used by other sub-engines (MCTS, Nemesis, etc) to query the sovereign LLM."""
        if not self.client:
            return ""
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            outputs = self.client(messages, max_new_tokens=max_tokens, temperature=temperature, do_sample=True)
            return outputs[0]["generated_text"][-1]["content"].strip()
        except Exception as e:
            print(f"Generic inference failed: {e}")
            return ""
