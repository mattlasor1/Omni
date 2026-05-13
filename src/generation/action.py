from __future__ import annotations

import json
import re

from src.learning.reasoning import CognitiveReasoningEngine


class ProceduralActionEngine:
    """
    Translates semantic knowledge into local, offline-safe procedural actions.
    """

    def __init__(self, reasoning_engine: CognitiveReasoningEngine):
        self.reasoning = reasoning_engine

    def _extract_path(self, situation_context: str) -> str | None:
        patterns = [
            r"([A-Za-z]:\\[^\n\r\"]+)",
            r"((?:\.{0,2}[\\/])?[A-Za-z0-9_\-./\\]+(?:[\\/][A-Za-z0-9_\-./\\]+)+)",
            r"([A-Za-z0-9_\-.]+\.(?:sql|py|ya?ml|md|txt))",
        ]
        for pattern in patterns:
            match = re.search(pattern, situation_context)
            if match:
                return match.group(1).strip().rstrip(".,)")
        return None

    def _looks_like_artifact_path(self, path: str | None) -> bool:
        if not path:
            return False
        return any(path.lower().endswith(suffix) for suffix in (".sql", ".py", ".yml", ".yaml", ".md", ".txt"))

    def _heuristic_action(self, situation_context: str) -> dict:
        query = situation_context.lower()
        path = self._extract_path(situation_context)
        if any(token in query for token in ["task evaluation", "task eval", "benchmark", "run eval", "run evaluation", "skill evaluation"]):
            return {"action": "evaluation:run", "reason": "Run the local owner-model evaluation rubric."}
        if path and any(token in query for token in ["import", "ingest", "train on"]):
            return {"action": f"workspace:import:{path}", "reason": "Import local evidence into the owner model."}
        if path and self._looks_like_artifact_path(path) and any(token in query for token in ["analyze", "scan", "review", "inspect"]):
            return {"action": f"artifact:review:{path}", "reason": "Review a local artifact against the owner adaptation model."}
        if path and any(token in query for token in ["analyze", "scan", "review", "inspect"]):
            return {"action": f"workspace:analyze:{path}", "reason": "Analyze a local workspace for owner-model signals."}
        if any(token in query for token in ["self-evaluate", "self evaluate", "evaluate yourself", "what is missing", "gap", "remediation", "readiness"]):
            return {"action": "training:review", "reason": "Run the local self-review loop and surface remediation work."}
        if any(token in query for token in ["plan", "build", "design", "debug", "improve", "fix", "review", "recover", "triage"]):
            return {"action": f"plan:{situation_context}", "reason": "Offline planner can produce a local runbook."}
        if any(token in query for token in ["what do you know", "remember", "teach", "lesson", "sql", "pipeline"]):
            return {"action": f"search:{situation_context}", "reason": "Search local lessons and owner memory."}
        if any(token in query for token in ["profile", "career", "role"]):
            return {"action": "profile:status", "reason": "Inspect the active owner profile."}
        return {"action": "none", "reason": "No stronger local action selected."}

    def decide_action(self, situation_context: str, semantic_memories: list[str]) -> dict:
        if not self.reasoning.client:
            return self._heuristic_action(situation_context)

        memory_block = "\n".join(f"- {memory}" for memory in semantic_memories)
        prompt = (
            f"Situation: {situation_context}\n\n"
            f"Relevant Knowledge:\n{memory_block}\n\n"
            "Choose one of these offline-safe actions when useful: "
            "`none`, `search:<topic>`, `plan:<task>`, `profile:status`, `training:plan`, `training:review`, "
            "`training:remediation`, `artifact:review:<path>`, `evaluation:run`, `evolve:<capability>`.\n"
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
