from __future__ import annotations

from typing import Any, Dict, List

import torch
from transformers import pipeline

from src.runtime import get_settings


class CognitiveReasoningEngine:
    """
    Local-first reasoning engine.
    It only loads a bundled local model in strict offline mode and otherwise
    degrades to deterministic heuristics. Prompting is string-based so it works
    with text-generation pipelines instead of depending on chat dict support.
    """

    def __init__(self):
        print("Initializing Sovereign Reasoning Engine (Local LLM)...")
        self.settings = get_settings()
        self.model_id = "HuggingFaceTB/SmolLM-135M-Instruct"
        self.client = self._load_local_pipeline()

    def _resolve_model_source(self) -> str | None:
        bundled = self.settings.model_dir / "smollm"
        if bundled.exists():
            return str(bundled)
        if self.settings.offline_strict or not self.settings.enable_model_downloads:
            return None
        return self.model_id

    def _load_local_pipeline(self):
        model_source = self._resolve_model_source()
        if model_source is None:
            print("No bundled local LLM found. Falling back to offline heuristics.")
            return None

        try:
            device = "cpu"
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"

            kwargs = {
                "task": "text-generation",
                "model": model_source,
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

    def _build_prompt(self, system_prompt: str, user_prompt: str) -> str:
        tokenizer = getattr(self.client, "tokenizer", None) if self.client else None
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        if tokenizer and hasattr(tokenizer, "apply_chat_template"):
            try:
                return tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except Exception:
                pass
        return (
            "System:\n"
            f"{system_prompt}\n\n"
            "User:\n"
            f"{user_prompt}\n\n"
            "Assistant:\n"
        )

    def _complete(self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float) -> str:
        if not self.client:
            return ""

        prompt = self._build_prompt(system_prompt, user_prompt)
        tokenizer = getattr(self.client, "tokenizer", None)
        generation_kwargs = {
            "max_new_tokens": max_tokens,
            "do_sample": temperature > 0,
            "temperature": temperature if temperature > 0 else 0.1,
            "return_full_text": False,
        }
        if tokenizer is not None:
            eos_token_id = getattr(tokenizer, "eos_token_id", None)
            if eos_token_id is not None:
                generation_kwargs["pad_token_id"] = eos_token_id

        outputs = self.client(prompt, **generation_kwargs)
        if not outputs:
            return ""

        generated = outputs[0].get("generated_text", "")
        if isinstance(generated, str):
            return generated.strip()
        if isinstance(generated, list):
            tail = generated[-1] if generated else {}
            if isinstance(tail, dict):
                return str(tail.get("content", "")).strip()
            return str(tail).strip()
        return str(generated).strip()

    def _heuristic_response(self, query: str, semantic_context: List[str]) -> str:
        if not semantic_context:
            return (
                "I do not have enough grounded local training context yet. "
                "Add an owner profile and local lessons so I can answer from your own material."
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
            synthesis = self._complete(
                system_prompt="You are the abstraction layer of an offline digital twin.",
                user_prompt=prompt,
                max_tokens=100,
                temperature=0.4,
            )
            if not synthesis:
                return {"concept": "Synthesis error", "confidence": 0.0}
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
            response = self._complete(
                system_prompt="You are an offline digital twin. Use only retrieved local context.",
                user_prompt=prompt,
                max_tokens=200,
                temperature=0.6,
            )
            return response or self._heuristic_response(query, semantic_context)
        except Exception as exc:
            print(f"Response generation failed: {exc}")
            return self._heuristic_response(query, semantic_context)

    def _generate_generic(self, system_prompt: str, user_prompt: str, max_tokens: int = 150, temperature: float = 0.5) -> str:
        if not self.client:
            return ""
        try:
            return self._complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception as exc:
            print(f"Generic inference failed: {exc}")
            return ""
