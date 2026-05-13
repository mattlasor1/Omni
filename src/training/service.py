from __future__ import annotations

import json
import threading
import time
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

from src.runtime import get_settings
from src.training.data_engineer import DataEngineerSkillPack
from src.training.workspace import WorkspaceAnalyzer


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
    _file_lock = threading.RLock()

    def __init__(self):
        self.settings = get_settings()
        self.path = self.settings.training_store_path
        self._lock = TrainingService._file_lock
        self._state = self._load()

    def _default_state(self) -> dict:
        return {
            "active_profile_id": None,
            "profiles": [],
            "lessons": [],
            "evaluations": [],
            "workspace_snapshots": [],
            "interactions": [],
            "self_reviews": [],
            "remediation_queue": [],
            "artifact_reviews": [],
            "task_evaluations": [],
        }

    def _normalize_profile(self, profile: dict) -> dict:
        normalized = deepcopy(profile)
        normalized.setdefault("goals", [])
        normalized.setdefault("constraints", ["Run entirely offline", "Use only local knowledge and tools"])
        normalized.setdefault("competencies", [])
        normalized.setdefault("tool_preferences", [])
        normalized.setdefault("created_at", _now())
        normalized.setdefault("updated_at", normalized["created_at"])
        for competency in normalized["competencies"]:
            competency.setdefault("target_evidence", 1)
            competency["evidence_ids"] = list(dict.fromkeys(competency.get("evidence_ids", [])))
        return normalized

    def _normalize_state(self, state: dict) -> dict:
        defaults = self._default_state()
        for key, value in defaults.items():
            state.setdefault(key, deepcopy(value))
        state["profiles"] = [self._normalize_profile(profile) for profile in state["profiles"]][-10:]
        state["lessons"] = state["lessons"][-500:]
        state["evaluations"] = state["evaluations"][-200:]
        state["workspace_snapshots"] = state["workspace_snapshots"][-10:]
        state["interactions"] = state["interactions"][-200:]
        state["self_reviews"] = state["self_reviews"][-100:]
        state["remediation_queue"] = state["remediation_queue"][-50:]
        state["artifact_reviews"] = state["artifact_reviews"][-200:]
        state["task_evaluations"] = state["task_evaluations"][-100:]
        return state

    def _load(self) -> dict:
        if self.path.exists():
            try:
                with self.path.open("r", encoding="utf-8") as handle:
                    return self._normalize_state(json.load(handle))
            except json.JSONDecodeError:
                pass
        return self._normalize_state(self._default_state())

    def _save(self) -> None:
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(self._state, handle, indent=2)

    def _refresh(self) -> None:
        with self._lock:
            self._state = self._load()

    def _get_active_profile_locked(self) -> dict | None:
        profile_id = self._state.get("active_profile_id")
        if not profile_id:
            return None
        for profile in self._state["profiles"]:
            if profile["id"] == profile_id:
                return profile
        return None

    def _find_lesson_locked(self, lesson: dict) -> dict | None:
        for existing in self._state["lessons"]:
            if (
                existing.get("profile_id") == lesson.get("profile_id")
                and existing.get("title") == lesson.get("title")
                and existing.get("lesson_type") == lesson.get("lesson_type")
                and existing.get("source_id") == lesson.get("source_id")
            ):
                return existing
        return None

    def _attach_lesson_to_profile_locked(self, profile_id: str | None, lesson_id: str, skill_tags: list[str]) -> None:
        if not profile_id:
            return
        for stored_profile in self._state["profiles"]:
            if stored_profile["id"] != profile_id:
                continue
            for competency in stored_profile["competencies"]:
                haystack = " ".join([competency["name"], competency["label"], competency["description"]]).lower()
                if any(tag.lower() in haystack for tag in skill_tags):
                    if lesson_id not in competency["evidence_ids"]:
                        competency["evidence_ids"].append(lesson_id)
            stored_profile["updated_at"] = _now()

    def _scenario_key(self, scenario: dict) -> str:
        return f"{scenario.get('name', 'scenario')}::{scenario.get('goal', '')}"

    def _scenario_tokens(self, scenario: dict) -> set[str]:
        competencies = " ".join(scenario.get("competencies", []))
        return _tokenize(" ".join([scenario.get("name", ""), scenario.get("goal", ""), competencies]))

    def _skill_pack_for_profile(self, profile: dict | None) -> DataEngineerSkillPack | None:
        if not profile:
            return None
        if profile.get("template_id") == "data_engineer" or profile.get("label") == "Data Engineer":
            return DataEngineerSkillPack()
        return None

    def _resolve_artifact_path(self, artifact_path: str, snapshot: dict | None = None) -> Path:
        requested = Path(artifact_path).expanduser()
        if requested.is_absolute():
            return requested.resolve()

        if snapshot and snapshot.get("workspace_path"):
            workspace_candidate = Path(snapshot["workspace_path"]).expanduser().resolve() / requested
            if workspace_candidate.exists():
                return workspace_candidate.resolve()

        project_candidate = self.settings.project_root / requested
        if project_candidate.exists():
            return project_candidate.resolve()

        return requested.resolve()

    def _order_remediation_queue(self, queue: list[dict], limit: int = 20) -> list[dict]:
        deduped = {}
        for item in queue:
            deduped[item["recommendation"]] = item
        ordered = list(deduped.values())
        ordered.sort(key=lambda item: {"high": 0, "medium": 1, "low": 2}.get(item["priority"], 3))
        return ordered[:limit]

    def _task_remediation_items(self, task_evaluation: dict | None) -> list[dict]:
        if not task_evaluation or task_evaluation.get("status") == "unconfigured":
            return []
        queue = []
        for task in task_evaluation.get("tasks", []):
            if task.get("status") == "ready":
                continue
            queue.append(
                {
                    "id": str(uuid.uuid4()),
                    "title": f"Skill task: {task.get('name', 'Task')}",
                    "recommendation": task.get("next_step", "Import more local evidence for this task."),
                    "priority": "high" if float(task.get("score", 0.0)) < 50 else "medium",
                    "competencies": [task.get("name", "Task")],
                    "created_at": _now(),
                    "status": "open",
                    "source": "task_evaluation",
                }
            )
        return queue

    def list_templates(self) -> list[dict]:
        return [
            {"template_id": template_id, **deepcopy(template)}
            for template_id, template in PROFILE_TEMPLATES.items()
        ]

    def get_skill_pack_definition(self) -> dict:
        profile = self.get_active_profile()
        skill_pack = self._skill_pack_for_profile(profile)
        if not skill_pack:
            return {
                "status": "unconfigured",
                "message": "No profession-specific skill pack is active for the current profile.",
            }
        return {"status": "active", "skill_pack": skill_pack.definition()}

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
            self._state = self._load()
            self._state["profiles"].append(profile)
            self._state["profiles"] = self._state["profiles"][-10:]
            self._state["active_profile_id"] = profile["id"]
            self._save()
        return deepcopy(profile)

    def get_active_profile(self) -> dict | None:
        self._refresh()
        profile = self._get_active_profile_locked()
        return deepcopy(profile) if profile else None

    def add_lesson(
        self,
        title: str,
        content: str,
        skill_tags: list[str] | None = None,
        lesson_type: str = "principle",
        source_id: str = "manual",
        counts_as_evidence: bool = True,
    ) -> dict:
        self._refresh()
        profile = self._get_active_profile_locked()
        lesson = {
            "id": str(uuid.uuid4()),
            "profile_id": profile["id"] if profile else None,
            "title": title,
            "content": content,
            "skill_tags": sorted(set(skill_tags or [])),
            "lesson_type": lesson_type,
            "source_id": source_id,
            "counts_as_evidence": counts_as_evidence,
            "created_at": _now(),
            "updated_at": _now(),
        }
        with self._lock:
            self._state = self._load()
            existing = self._find_lesson_locked(lesson)
            if existing:
                existing["content"] = content
                existing["skill_tags"] = sorted(set(existing.get("skill_tags", [])) | set(lesson["skill_tags"]))
                existing["counts_as_evidence"] = existing.get("counts_as_evidence", True) or counts_as_evidence
                existing["updated_at"] = _now()
                if existing.get("counts_as_evidence", True):
                    self._attach_lesson_to_profile_locked(existing.get("profile_id"), existing["id"], existing.get("skill_tags", []))
                self._save()
                return deepcopy(existing)

            self._state["lessons"].append(lesson)
            self._state["lessons"] = self._state["lessons"][-500:]
            if counts_as_evidence:
                self._attach_lesson_to_profile_locked(lesson["profile_id"], lesson["id"], lesson["skill_tags"])
            self._save()
        return deepcopy(lesson)

    def search_lessons(self, query: str, limit: int = 5) -> list[dict]:
        self._refresh()
        query_tokens = _tokenize(query)
        ranked = []
        for lesson in self._state["lessons"]:
            lesson_tokens = _tokenize(" ".join([lesson["title"], lesson["content"], " ".join(lesson.get("skill_tags", []))]))
            overlap = len(query_tokens & lesson_tokens)
            if overlap:
                ranked.append((overlap, lesson.get("updated_at", lesson.get("created_at", 0.0)), lesson))
        ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return [deepcopy(lesson) for _, _, lesson in ranked[:limit]]

    def get_context_blocks(self, query: str, limit: int = 4) -> list[str]:
        blocks = []
        profile = self.get_active_profile()
        if profile:
            goals = ", ".join(profile["goals"]) if profile["goals"] else "No explicit goals captured yet."
            blocks.append(f"Active twin profile: {profile['display_name']} ({profile['label']}). Goals: {goals}")
        snapshot = self.get_latest_workspace_snapshot()
        if snapshot:
            frameworks = ", ".join(snapshot.get("frameworks", [])) or "local patterns"
            blocks.append(f"Latest workspace snapshot: {snapshot.get('summary', '')} Frameworks: {frameworks}")
            for artifact in snapshot.get("artifacts", [])[:2]:
                blocks.append(f"Artifact {artifact['path']}: {artifact['summary']}")
        for lesson in self.search_lessons(query, limit=limit):
            blocks.append(f"{lesson['title']}: {lesson['content']}")
        return blocks

    def build_training_plan(self) -> dict:
        self._refresh()
        profile = self._get_active_profile_locked()
        if not profile:
            return {
                "status": "unconfigured",
                "message": "No active profession profile. Create one before training.",
                "next_steps": ["Select a profession template", "Define goals", "Import a local workspace or add domain lessons"],
            }

        next_steps = []
        if not self.get_latest_workspace_snapshot():
            next_steps.append("Import a local workspace so Omni can learn from real artifacts, not only hand-written lessons.")
        for competency in profile["competencies"]:
            evidence_count = len(competency["evidence_ids"])
            if evidence_count < competency["target_evidence"]:
                next_steps.append(
                    f"Add {competency['target_evidence'] - evidence_count} more lesson(s) for {competency['label']}."
                )

        for item in self.get_remediation_queue(limit=3):
            next_steps.append(item["recommendation"])

        task_evaluation = self.get_latest_task_evaluation()
        if task_evaluation:
            for task in task_evaluation.get("tasks", []):
                if task.get("status") != "ready" and task.get("next_step"):
                    next_steps.append(task["next_step"])

        if not next_steps:
            next_steps.append("Run domain evaluations and keep using Omni on live tasks so the self-review loop can refine it.")

        deduped_steps = list(dict.fromkeys(next_steps))
        return {
            "status": "ready" if len(deduped_steps) == 1 and "Run domain evaluations" in deduped_steps[0] else "training",
            "profile": deepcopy(profile),
            "next_steps": deduped_steps,
        }

    def evaluate_readiness(self, persist: bool = True) -> dict:
        self._refresh()
        profile = self._get_active_profile_locked()
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
        previous_score = self._state["evaluations"][-1]["readiness_score"] if self._state["evaluations"] else 0.0
        evaluation = {
            "timestamp": _now(),
            "readiness_score": readiness,
            "trend_delta": round(readiness - previous_score, 2),
            "competencies": deepcopy(competency_scores),
        }
        if persist:
            with self._lock:
                self._state = self._load()
                self._state["evaluations"].append(evaluation)
                self._state["evaluations"] = self._state["evaluations"][-200:]
                self._save()
        return {
            "status": "ready" if readiness >= 0.8 else "training",
            "readiness_score": readiness,
            "competencies": competency_scores,
            "gaps": gaps,
            "trend_delta": evaluation["trend_delta"],
        }

    def export_snapshot(self) -> dict:
        self._refresh()
        return deepcopy(self._state)

    def review_artifact(self, artifact_path: str) -> dict:
        snapshot = self.get_latest_workspace_snapshot()
        profile = self.get_active_profile()
        skill_pack = self._skill_pack_for_profile(profile) or DataEngineerSkillPack()
        resolved_path = self._resolve_artifact_path(artifact_path, snapshot)
        workspace_root = snapshot.get("workspace_path") if snapshot else resolved_path.parent
        review = skill_pack.review_artifact(resolved_path, workspace_root=workspace_root)
        review["profile_id"] = profile["id"] if profile else None

        findings = review.get("findings", [])
        finding_text = "; ".join(
            f"{finding['severity']}: {finding['title']} -> {finding['recommendation']}"
            for finding in findings[:3]
        ) or "No obvious findings from the local rubric."
        lesson = self.add_lesson(
            title=f"Artifact review: {review['path']}",
            content=f"{review['summary']} {finding_text}",
            skill_tags=[finding.get("competency", "").lower().replace(" ", "_") for finding in findings if finding.get("competency")],
            lesson_type="artifact_review",
            source_id=f"artifact_review:{review['absolute_path']}",
            counts_as_evidence=False,
        )
        review["lesson_id"] = lesson["id"]

        with self._lock:
            self._state = self._load()
            self._state["artifact_reviews"].append(review)
            self._state["artifact_reviews"] = self._state["artifact_reviews"][-200:]
            self._save()
        return deepcopy(review)

    def get_recent_artifact_reviews(self, limit: int = 20) -> list[dict]:
        self._refresh()
        return deepcopy(self._state.get("artifact_reviews", [])[-limit:])

    def run_task_evaluation(self, persist: bool = True) -> dict:
        snapshot = self.get_latest_workspace_snapshot()
        profile = self.get_active_profile()
        skill_pack = self._skill_pack_for_profile(profile) or DataEngineerSkillPack()
        evaluation = skill_pack.evaluate_workspace(snapshot)
        evaluation["profile_id"] = profile["id"] if profile else None
        evaluation["workspace_path"] = snapshot.get("workspace_path") if snapshot else None

        if persist:
            with self._lock:
                self._state = self._load()
                self._state["task_evaluations"].append(evaluation)
                self._state["task_evaluations"] = self._state["task_evaluations"][-100:]
                self._state["remediation_queue"] = self._order_remediation_queue(
                    self._state.get("remediation_queue", []) + self._task_remediation_items(evaluation),
                    limit=50,
                )
                self._save()
        return deepcopy(evaluation)

    def get_latest_task_evaluation(self) -> dict | None:
        self._refresh()
        evaluations = self._state.get("task_evaluations", [])
        if not evaluations:
            return None
        return deepcopy(evaluations[-1])

    def build_task_plan(self, task: str) -> str:
        profile = self.get_active_profile()
        label = profile["label"] if profile else "General Professional"
        snapshot = self.get_latest_workspace_snapshot()
        framework_hint = ", ".join(snapshot.get("frameworks", [])) if snapshot else "local tools"
        plan = [
            f"Clarify the objective and success criteria for: {task}",
            f"Map the request to {label.lower()} competencies already captured in local lessons.",
            f"Choose the lowest-risk implementation path that stays within verified offline knowledge and {framework_hint}.",
            "Produce a runbook, checklist, or response the user can act on immediately.",
        ]
        return " | ".join(plan)

    def get_latest_workspace_snapshot(self) -> dict | None:
        self._refresh()
        snapshots = self._state.get("workspace_snapshots", [])
        if not snapshots:
            return None
        return deepcopy(snapshots[-1])

    def record_interaction(
        self,
        query: str,
        response: str,
        context_blocks: list[str] | None = None,
        process_used: str | None = None,
        action_decided: dict | None = None,
        action_result: str | None = None,
        action_paused: bool = False,
    ) -> dict:
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": _now(),
            "query": query,
            "response": response,
            "context_blocks": (context_blocks or [])[:8],
            "process_used": process_used or "unknown",
            "action_decided": deepcopy(action_decided) if action_decided else None,
            "action_result": action_result,
            "action_paused": action_paused,
        }
        with self._lock:
            self._state = self._load()
            self._state["interactions"].append(entry)
            self._state["interactions"] = self._state["interactions"][-200:]
            self._save()
        return deepcopy(entry)

    def get_recent_interactions(self, limit: int = 20) -> list[dict]:
        self._refresh()
        return deepcopy(self._state.get("interactions", [])[-limit:])

    def _default_scenarios_for_profile(self, profile: dict) -> list[dict]:
        scenarios = []
        for competency in profile.get("competencies", [])[:4]:
            scenarios.append(
                {
                    "name": f"{competency['label']} Drill",
                    "goal": f"Demonstrate practical judgment for {competency['label'].lower()} using only local artifacts and lessons.",
                    "competencies": [competency["label"]],
                }
            )
        return scenarios

    def _evaluate_scenario(self, scenario: dict, snapshot: dict | None, profile: dict, interactions: list[dict]) -> dict:
        scenario_tokens = self._scenario_tokens(scenario)
        competency_tokens = {
            token
            for competency in profile.get("competencies", [])
            for token in _tokenize(" ".join([competency["name"], competency["label"]]))
            if competency["label"] in scenario.get("competencies", []) or competency["name"] in scenario.get("competencies", [])
        }
        scenario_tokens |= competency_tokens

        external_hits = 0
        reflection_hits = 0
        supporting_lessons = []
        for lesson in self._state["lessons"]:
            lesson_tokens = _tokenize(" ".join([lesson["title"], lesson["content"], " ".join(lesson.get("skill_tags", []))]))
            if not lesson_tokens or not (scenario_tokens & lesson_tokens):
                continue
            if lesson.get("counts_as_evidence", True):
                external_hits += 1
            else:
                reflection_hits += 1
            if len(supporting_lessons) < 3:
                supporting_lessons.append(lesson["title"])

        artifact_hits = 0
        supporting_artifacts = []
        if snapshot:
            for artifact in snapshot.get("artifacts", []):
                artifact_tokens = _tokenize(" ".join([
                    artifact.get("path", ""),
                    artifact.get("summary", ""),
                    " ".join(artifact.get("skill_tags", [])),
                    " ".join(artifact.get("frameworks", [])),
                ]))
                if not artifact_tokens or not (scenario_tokens & artifact_tokens):
                    continue
                artifact_hits += 1
                if len(supporting_artifacts) < 3:
                    supporting_artifacts.append(artifact["path"])

        interaction_hits = 0
        for interaction in interactions:
            interaction_tokens = _tokenize(" ".join([
                interaction.get("query", ""),
                interaction.get("response", ""),
                interaction.get("action_result", "") or "",
            ]))
            if interaction_tokens and (scenario_tokens & interaction_tokens):
                interaction_hits += 1

        external_score = min(1.0, external_hits / 2.0)
        artifact_score = min(1.0, artifact_hits / 2.0)
        interaction_score = min(1.0, interaction_hits / 3.0)
        reflection_bonus = min(0.15, reflection_hits * 0.05)
        coverage = round(min(1.0, (external_score * 0.55) + (artifact_score * 0.25) + (interaction_score * 0.20) + reflection_bonus), 2)

        return {
            "name": scenario.get("name", "Scenario"),
            "goal": scenario.get("goal", ""),
            "competencies": scenario.get("competencies", []),
            "coverage_score": coverage,
            "status": "ready" if coverage >= 0.65 else "gap",
            "external_lesson_hits": external_hits,
            "reflection_hits": reflection_hits,
            "artifact_hits": artifact_hits,
            "interaction_hits": interaction_hits,
            "supporting_lessons": supporting_lessons,
            "supporting_artifacts": supporting_artifacts,
        }

    def _build_remediation_queue(self, readiness: dict, scenario_results: list[dict], snapshot: dict | None) -> list[dict]:
        queue = []
        for scenario in scenario_results:
            if scenario["coverage_score"] >= 0.65:
                continue
            queue.append(
                {
                    "id": str(uuid.uuid4()),
                    "title": scenario["name"],
                    "recommendation": f"Close the {scenario['name']} gap: {scenario['goal']}",
                    "priority": "high" if scenario["coverage_score"] < 0.35 else "medium",
                    "competencies": scenario.get("competencies", []),
                    "created_at": _now(),
                    "status": "open",
                }
            )

        for gap in readiness.get("gaps", []):
            queue.append(
                {
                    "id": str(uuid.uuid4()),
                    "title": gap.split(" needs", 1)[0],
                    "recommendation": gap,
                    "priority": "medium",
                    "competencies": [gap.split(" needs", 1)[0]],
                    "created_at": _now(),
                    "status": "open",
                }
            )

        if snapshot:
            for step in snapshot.get("recommended_next_steps", [])[:3]:
                queue.append(
                    {
                        "id": str(uuid.uuid4()),
                        "title": "Workspace Next Step",
                        "recommendation": step,
                        "priority": "low",
                        "competencies": [],
                        "created_at": _now(),
                        "status": "open",
                    }
                )

        return self._order_remediation_queue(queue, limit=20)

    def _generate_reflection_lessons(self, profile: dict, scenario_results: list[dict], snapshot: dict | None) -> list[dict]:
        generated = []
        for scenario in scenario_results:
            if scenario["coverage_score"] >= 0.85:
                continue
            if scenario["external_lesson_hits"] + scenario["artifact_hits"] < 2:
                continue
            supporting = []
            if scenario["supporting_lessons"]:
                supporting.append("Lessons: " + ", ".join(scenario["supporting_lessons"]))
            if scenario["supporting_artifacts"]:
                supporting.append("Artifacts: " + ", ".join(scenario["supporting_artifacts"]))
            if snapshot and snapshot.get("frameworks"):
                supporting.append("Frameworks: " + ", ".join(snapshot["frameworks"][:4]))
            content = (
                f"Self-review synthesis for {scenario['name']}. "
                f"Current coverage score: {scenario['coverage_score']}. "
                f"Focus area: {scenario['goal']} "
                + " ".join(supporting)
            )
            lesson = self.add_lesson(
                title=f"Self-review synthesis: {scenario['name']}",
                content=content,
                skill_tags=[competency.lower().replace(" ", "_") for competency in scenario.get("competencies", [])],
                lesson_type="self_reflection",
                source_id=f"self_review:{profile['id']}:{scenario['name']}",
                counts_as_evidence=False,
            )
            generated.append({"lesson_id": lesson["id"], "title": lesson["title"]})
        return generated

    def run_self_review(self, trigger: str = "manual", persist: bool = True, generate_reflections: bool = True) -> dict:
        self._refresh()
        profile = self._get_active_profile_locked()
        if not profile:
            return {
                "status": "unconfigured",
                "trigger": trigger,
                "readiness_score": 0.0,
                "gaps": ["No active profession profile."],
                "scenario_results": [],
                "remediation_queue": [],
            }

        snapshot = self.get_latest_workspace_snapshot()
        readiness = self.evaluate_readiness(persist=False)
        scenarios = deepcopy(snapshot.get("evaluation_scenarios", [])) if snapshot else []
        if not scenarios:
            scenarios = self._default_scenarios_for_profile(profile)
        interactions = self.get_recent_interactions(limit=20)
        scenario_results = [self._evaluate_scenario(scenario, snapshot, profile, interactions) for scenario in scenarios]
        strengths = [result["name"] for result in scenario_results if result["status"] == "ready"]
        task_evaluation = self.run_task_evaluation(persist=False)
        remediation_queue = self._build_remediation_queue(readiness, scenario_results, snapshot)
        remediation_queue = self._order_remediation_queue(remediation_queue + self._task_remediation_items(task_evaluation))
        generated_reflections = self._generate_reflection_lessons(profile, scenario_results, snapshot) if generate_reflections else []

        previous_review = self.get_latest_self_review()
        previous_score = previous_review.get("readiness_score", 0.0) if previous_review else 0.0
        review = {
            "timestamp": _now(),
            "trigger": trigger,
            "status": "ready" if readiness["readiness_score"] >= 0.8 and not remediation_queue else "training",
            "readiness_score": readiness["readiness_score"],
            "trend_delta": round(readiness["readiness_score"] - previous_score, 2),
            "strengths": strengths,
            "gaps": readiness.get("gaps", []),
            "scenario_results": scenario_results,
            "task_evaluation": task_evaluation,
            "remediation_queue": remediation_queue,
            "generated_reflections": generated_reflections,
            "recent_interaction_count": len(interactions),
        }

        if persist:
            with self._lock:
                self._state = self._load()
                self._state["self_reviews"].append(review)
                self._state["self_reviews"] = self._state["self_reviews"][-100:]
                self._state["remediation_queue"] = remediation_queue
                self._save()
        return review

    def run_improvement_cycle(self, trigger: str = "manual") -> dict:
        return self.run_self_review(trigger=trigger, persist=True, generate_reflections=True)

    def get_latest_self_review(self) -> dict | None:
        self._refresh()
        reviews = self._state.get("self_reviews", [])
        if not reviews:
            return None
        return deepcopy(reviews[-1])

    def get_remediation_queue(self, limit: int = 10) -> list[dict]:
        self._refresh()
        return deepcopy(self._state.get("remediation_queue", [])[:limit])

    def analyze_workspace(self, workspace_path: str, max_files: int = 200) -> dict:
        profile = self.get_active_profile()
        analyzer = WorkspaceAnalyzer(workspace_path)
        return analyzer.analyze(profile=profile, max_files=max_files)

    def import_workspace(self, workspace_path: str, max_files: int = 200, lesson_limit: int = 20) -> dict:
        report = self.analyze_workspace(workspace_path, max_files=max_files)
        before_ids = {lesson["id"] for lesson in self.export_snapshot().get("lessons", [])}
        for artifact in report.get("artifacts", [])[:lesson_limit]:
            self.add_lesson(
                title=f"Workspace artifact: {artifact['name']}",
                content=artifact["summary"],
                skill_tags=artifact.get("skill_tags", []),
                lesson_type=artifact.get("kind", "workspace_artifact"),
                source_id=artifact.get("path", workspace_path),
            )

        self.add_lesson(
            title=f"Workspace summary: {report['workspace_name']}",
            content=report["summary"],
            skill_tags=list(report.get("skill_signals", {}).keys())[:4],
            lesson_type="workspace_summary",
            source_id=report["workspace_path"],
        )
        after_ids = {lesson["id"] for lesson in self.export_snapshot().get("lessons", [])}
        imported = len(after_ids - before_ids)

        snapshot = {
            "workspace_path": report["workspace_path"],
            "workspace_name": report["workspace_name"],
            "summary": report["summary"],
            "frameworks": report["frameworks"],
            "artifact_counts": report["artifact_counts"],
            "skill_signals": report["skill_signals"],
            "artifacts": report["artifacts"][:10],
            "recommended_next_steps": report["recommended_next_steps"],
            "evaluation_scenarios": report["evaluation_scenarios"],
            "created_at": _now(),
            "imported_lessons": imported,
        }
        with self._lock:
            self._state = self._load()
            self._state["workspace_snapshots"] = [
                existing
                for existing in self._state["workspace_snapshots"]
                if existing.get("workspace_path") != snapshot["workspace_path"]
            ]
            self._state["workspace_snapshots"].append(snapshot)
            self._state["workspace_snapshots"] = self._state["workspace_snapshots"][-10:]
            self._save()

        review = self.run_self_review(trigger="workspace_import", persist=True, generate_reflections=True)
        task_evaluation = self.run_task_evaluation(persist=True)
        report["imported_lessons"] = imported
        report["self_review"] = review
        report["task_evaluation"] = task_evaluation
        return report
