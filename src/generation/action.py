from __future__ import annotations

import json

from src.learning.reasoning import CognitiveReasoningEngine


class ProceduralActionEngine:
    """
    Translates semantic knowledge into local, offline-safe procedural actions.
    """

    def __init__(self, reasoning_engine: CognitiveReasoningEngine):
        self.reasoning = reasoning_engine

    def _heuristic_action(self, situation_context: str) -> dict:
        query = situation_context.lower()
        if any(token in query for token in ["plan", "build", "design", "debug", "improve", "fix"]):
            return {"action": f"plan:{situation_context}", "reason": "Offline planner can produce a local runbook."}
        if any(token in query for token in ["what do you know", "remember", "teach", "lesson", "sql", "pipeline"]):
            return {"action": f"search:{situation_context}", "reason": "Search local lessons and profession memory."}
        if any(token in query for token in ["profile", "career", "role"]):
            return {"action": "profile:status", "reason": "Inspect the active profession profile."}
        return {"action": "none", "reason": "No stronger local action selected."}

    def decide_action(self, situation_context: str, semantic_memories: list[str]) -> dict:
        if not self.reasoning.client:
            return self._heuristic_action(situation_context)

        memory_block = "\n".join(f"- {memory}" for memory in semantic_memories)
        prompt = (
            f"Situation: {situation_context}\n\n"
            f"Relevant Knowledge:\n{memory_block}\n\n"
            "Choose one of these offline-safe actions when useful: "
            "`none`, `search:<topic>`, `plan:<task>`, `profile:status`, `training:plan`, `evolve:<capability>`.\n"
            "Output raw JSON with keys `action` and `reason`."
        )

        try:
            action_str = self.reasoning._generate_generic(
                system_prompt="You map local knowledge to offline-safe JSON actions. Respond only with JSON.",
                user_prompt=prompt,
                max_tokens=150,
                temperature=0.2,
            )
            if "{" in action_str and "}" in action_str:
                action_str = "{" + action_str.split("{", 1)[1].rsplit("}", 1)[0] + "}"
            return json.loads(action_str)
        except Exception as exc:
            print(f"Action generation failed: {exc}")
            return self._heuristic_action(situation_context)
