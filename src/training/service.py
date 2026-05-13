from __future__ import annotations

import json
import threading
import time
import uuid
from copy import deepcopy
from typing import Any, Dict, List

from src.runtime import get_settings


PROFILE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "data_engineer": {
        "label": "Data Engineer",
        "summary": "Designs, operates, and improves data platforms, pipelines, and warehouse models.",
        "competencies": [
            {"name": "sql_modeling", "label": "SQL Modeling", "description": "Design schemas, joins, transformations, and warehouse-friendly SQL.", "target_evidence": 3},
            {"name": "orchestration", "label": "Orchestration", "description": "Schedule, recover, and reason about DAGs and dependencies.", "target_evidence": 3},
            {"name": "data_quality", "label": "Data Quality", "description": "Define tests, contracts, and anomaly handling.", "target_evidence": 2},
            {"name": "performance", "label": "Performance", "description": "Tune compute, storage, and incremental workloads.", "target_evidence": 2},
            {"name": "incident_response", "label": "Incident Response", "description": "Triage failed loads, broken jobs, and stale datasets.", "target_evidence": 2},
            {"name": "communication", "label": "Communication", "description": "Explain tradeoffs, runbooks, and stakeholder-facing decisions clearly.", "target_evidence": 2},
        ],
        "tool_preferences": ["sql", "dbt", "airflow", "spark", "warehouse", "lineage", "git"],
    },
    "generic_professional": {
        "label": "General Professional",
        "summary": "Learns a user's domain, language, workflows, and decision standards from curated local knowledge.",
        "competencies": [
            {"name": "domain_knowledge", "label": "Domain Knowledge", "description": "Understands local terminology, rules, and objectives.", "target_evidence": 3},
            {"name": "workflows", "label": "Workflows", "description": "Knows how work gets done and where mistakes appear.", "target_evidence": 3},
            {"name": "decision_support", "label": "Decision Support", "description": "Explains options, risks, and next steps clearly.", "target_evidence": 2},
        ],
        "tool_preferences": ["documents", "spreadsheets", "notes"],
    },
}


def _now() -> float:
    return time.time()


def _tokenize(text: str) -> set[str]:
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in text)
    return {token for token in cleaned.split() if token}


class TrainingService:
    def __init__(self):
        self.settings = get_settings()
        self.path = self.settings.training_store_path
        self._lock = threading.Lock()
        self._state = self._load()

    def _default_state(self) -> dict:
        return {"active_profile_id": None, "profiles": [], "lessons": [], "evaluations": []}

    def _load(self) -> dict:
        if self.path.exists():
            try:
                with self.path.open("r", encoding="utf-8") as handle:
                    return json.load(handle)
            except json.JSONDecodeError:
                pass
        return self._default_state()

    def _save(self) -> None:
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(self._state, handle, indent=2)

    def _refresh(self) -> None:
        self._state = self._load()

    def list_templates(self) -> list[dict]:
        return [
            {"template_id": template_id, **deepcopy(template)}
            for template_id, template in PROFILE_TEMPLATES.items()
        ]

    def activate_profile(
        self,
        template_id: str,
        display_name: str | None = None,
        goals: list[str] | None = None,
        constraints: list[str] | None = None,
    ) -> dict:
        template = deepcopy(PROFILE_TEMPLATES.get(template_id, PROFILE_TEMPLATES["generic_professional"]))
        profile = {
            "id": str(uuid.uuid4()),
            "template_id": template_id if template_id in PROFILE_TEMPLATES else "generic_professional",
            "label": template["label"],
            "display_name": display_name or template["label"],
            "summary": template["summary"],
            "goals": goals or [],
            "constraints": constraints or ["Run entirely offline", "Use only local knowledge and tools"],
            "competencies": [
                {**competency, "evidence_ids": []}
                for competency in template["competencies"]
            ],
            "tool_preferences": template.get("tool_preferences", []),
            "created_at": _now(),
            "updated_at": _now(),
        }
        with self._lock:
            self._state["profiles"] = [profile]
            self._state["active_profile_id"] = profile["id"]
            self._save()
        return profile

    def get_active_profile(self) -> dict | None:
        self._refresh()
        profile_id = self._state.get("active_profile_id")
        if not profile_id:
            return None
        for profile in self._state["profiles"]:
            if profile["id"] == profile_id:
                return deepcopy(profile)
        return None

    def add_lesson(
        self,
        title: str,
        content: str,
        skill_tags: list[str] | None = None,
        lesson_type: str = "principle",
        source_id: str = "manual",
    ) -> dict:
        profile = self.get_active_profile()
        lesson = {
            "id": str(uuid.uuid4()),
            "profile_id": profile["id"] if profile else None,
            "title": title,
            "content": content,
            "skill_tags": skill_tags or [],
            "lesson_type": lesson_type,
            "source_id": source_id,
            "created_at": _now(),
        }
        with self._lock:
            self._state["lessons"].append(lesson)
            if profile:
                for stored_profile in self._state["profiles"]:
                    if stored_profile["id"] != profile["id"]:
                        continue
                    for competency in stored_profile["competencies"]:
                        haystack = " ".join([competency["name"], competency["label"], competency["description"]]).lower()
                        if any(tag.lower() in haystack for tag in lesson["skill_tags"]):
                            competency["evidence_ids"].append(lesson["id"])
                    stored_profile["updated_at"] = _now()
            self._save()
        return lesson

    def search_lessons(self, query: str, limit: int = 5) -> list[dict]:
        self._refresh()
        query_tokens = _tokenize(query)
        ranked = []
        for lesson in self._state["lessons"]:
            lesson_tokens = _tokenize(" ".join([lesson["title"], lesson["content"], " ".join(lesson["skill_tags"])]))
            overlap = len(query_tokens & lesson_tokens)
            if overlap:
                ranked.append((overlap, lesson))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [deepcopy(lesson) for _, lesson in ranked[:limit]]

    def get_context_blocks(self, query: str, limit: int = 4) -> list[str]:
        blocks = []
        profile = self.get_active_profile()
        if profile:
            goals = ", ".join(profile["goals"]) if profile["goals"] else "No explicit goals captured yet."
            blocks.append(f"Active twin profile: {profile['display_name']} ({profile['label']}). Goals: {goals}")
        for lesson in self.search_lessons(query, limit=limit):
            blocks.append(f"{lesson['title']}: {lesson['content']}")
        return blocks

    def build_training_plan(self) -> dict:
        self._refresh()
        profile = self.get_active_profile()
        if not profile:
            return {
                "status": "unconfigured",
                "message": "No active profession profile. Create one before training.",
                "next_steps": ["Select a profession template", "Define goals", "Add domain lessons and examples"],
            }

        next_steps = []
        for competency in profile["competencies"]:
            evidence_count = len(competency["evidence_ids"])
            if evidence_count < competency["target_evidence"]:
                next_steps.append(
                    f"Add {competency['target_evidence'] - evidence_count} more lesson(s) for {competency['label']}."
                )
        if not next_steps:
            next_steps.append("Run domain evaluations and start using Omni on live tasks.")

        return {
            "status": "ready" if len(next_steps) == 1 and next_steps[0].startswith("Run domain evaluations") else "training",
            "profile": profile,
            "next_steps": next_steps,
        }

    def evaluate_readiness(self, persist: bool = True) -> dict:
        self._refresh()
        profile = self.get_active_profile()
        if not profile:
            return {"status": "unconfigured", "readiness_score": 0.0, "gaps": ["No active profession profile."]}

        competency_scores = []
        gaps = []
        for competency in profile["competencies"]:
            evidence = len(competency["evidence_ids"])
            score = min(1.0, evidence / max(competency["target_evidence"], 1))
            competency_scores.append({"competency": competency["label"], "score": round(score, 2), "evidence": evidence})
            if score < 1.0:
                gaps.append(f"{competency['label']} needs more examples, runbooks, or corrections.")

        readiness = round(sum(item["score"] for item in competency_scores) / max(len(competency_scores), 1), 2)
        if persist:
            evaluation = {"timestamp": _now(), "readiness_score": readiness}
            with self._lock:
                self._state["evaluations"].append(evaluation)
                self._save()
        return {
            "status": "ready" if readiness >= 0.8 else "training",
            "readiness_score": readiness,
            "competencies": competency_scores,
            "gaps": gaps,
        }

    def export_snapshot(self) -> dict:
        self._refresh()
        return deepcopy(self._state)

    def build_task_plan(self, task: str) -> str:
        profile = self.get_active_profile()
        label = profile["label"] if profile else "General Professional"
        plan = [
            f"Clarify the objective and success criteria for: {task}",
            f"Map the request to {label.lower()} competencies already captured in local lessons.",
            "Choose the lowest-risk implementation path that stays within local tools and verified knowledge.",
            "Produce a runbook, checklist, or response the user can act on immediately.",
        ]
        return " | ".join(plan)
