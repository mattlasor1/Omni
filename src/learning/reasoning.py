from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import torch
from transformers import pipeline

from src.runtime import get_settings


class CognitiveReasoningEngine:
    """
    Local-first reasoning engine.
    It attempts to load bundled open-weight models without downloading anything
    at runtime. When no model bundle is present, it degrades to deterministic
    offline heuristics instead of failing.
    """

    def __init__(self):
        print("Initializing Sovereign Reasoning Engine (Local LLM)...")
        self.settings = get_settings()
        self.model_id = "HuggingFaceTB/SmolLM-135M-Instruct"
        self.client = self._load_local_pipeline()

    def _resolve_model_source(self) -> str:
        bundled = self.settings.model_dir / "smollm"
        if bundled.exists():
            return str(bundled)
        return self.model_id

    def _load_local_pipeline(self):
        try:
            device = "cpu"
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"

            kwargs = {
                "task": "text-generation",
                "model": self._resolve_model_source(),
                "device": device,
                "torch_dtype": torch.float16 if device != "cpu" else torch.float32,
            }
            if self.settings.offline_strict or not self.settings.enable_model_downloads:
                kwargs["local_files_only"] = True
            client = pipeline(**kwargs)
            print(f"Sovereign Engine Online ({device}).")
            return client
        except Exception as exc:
            print(f"Failed to load local LLM: {exc}. Falling back to offline heuristics.")
            return None

    def _heuristic_response(self, query: str, semantic_context: List[str]) -> str:
        if not semantic_context:
            return (
                "I do not have enough grounded local training context yet. "
                "Add a profession profile and domain lessons so I can answer from your own material."
            )

        lead = semantic_context[0]
        extras = semantic_context[1:3]
        response = f"From local twin memory, the strongest relevant guidance is: {lead}"
        if extras:
            response += " Supporting context: " + " | ".join(extras)
        response += f" Query handled offline: {query}"
        return response

    def synthesize_concept(self, memory_cluster: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self.client:
            return {
                "concept": f"Compressed local pattern across {len(memory_cluster)} observations.",
                "confidence": 0.75,
            }

        contexts = [entry.get("content", str(entry)) for entry in memory_cluster if entry.get("content")]
        prompt = (
            "Synthesize the following raw observations into a single, high-level abstract concept.\n\n"
            + "\n".join(f"{idx + 1}. {context}" for idx, context in enumerate(contexts))
        )
        try:
            messages = [
                {"role": "system", "content": "You are the abstraction layer of an offline digital twin."},
                {"role": "user", "content": prompt},
            ]
            outputs = self.client(messages, max_new_tokens=100, temperature=0.4, do_sample=True)
            synthesis = outputs[0]["generated_text"][-1]["content"].strip()
            return {"concept": synthesis, "confidence": 0.95}
        except Exception as exc:
            print(f"Cognitive synthesis failed: {exc}")
            return {"concept": "Synthesis error", "confidence": 0.0}

    def generate_response(self, query: str, semantic_context: List[str]) -> str:
        if not self.client:
            return self._heuristic_response(query, semantic_context)

        context_block = "\n".join(f"- {entry}" for entry in semantic_context)
        prompt = (
            f"Query: {query}\n\n"
            f"Relevant Semantic Memories:\n{context_block}\n\n"
            "Generate a thoughtful response grounded only in the provided local memories."
        )
        try:
            messages = [
                {"role": "system", "content": "You are an offline digital twin. Use only retrieved local context."},
                {"role": "user", "content": prompt},
            ]
            outputs = self.client(messages, max_new_tokens=200, temperature=0.6, do_sample=True)
            return outputs[0]["generated_text"][-1]["content"].strip()
        except Exception as exc:
            print(f"Response generation failed: {exc}")
            return self._heuristic_response(query, semantic_context)

    def _generate_generic(self, system_prompt: str, user_prompt: str, max_tokens: int = 150, temperature: float = 0.5) -> str:
        if not self.client:
            return ""
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            outputs = self.client(messages, max_new_tokens=max_tokens, temperature=temperature, do_sample=True)
            return outputs[0]["generated_text"][-1]["content"].strip()
        except Exception as exc:
            print(f"Generic inference failed: {exc}")
            return ""
