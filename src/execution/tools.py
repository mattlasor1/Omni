from __future__ import annotations

import time
from typing import Any, Dict

from src.execution.meta_learning import MetaLearningEngine
from src.training.service import TrainingService


class ExecutionRouter:
    """
    Local-only execution surface for the digital twin.
    The router focuses on offline-safe capabilities such as plan generation,
    local lesson retrieval, and profile introspection.
    """

    def __init__(self, cache_interface, meta_learning: MetaLearningEngine = None):
        self.cache = cache_interface
        self.meta = meta_learning
        self.training = TrainingService()

    def execute_action(self, action_json: Dict[str, Any]) -> str:
        action = action_json.get("action", "none")
        reason = action_json.get("reason", "unknown")
        print(f"Executing Action: {action} (Reason: {reason})")

        if action == "none":
            result = "Decided to take no action."
        elif action.startswith("workspace:analyze:"):
            path = action.split("workspace:analyze:", 1)[1].strip()
            report = self.training.analyze_workspace(path)
            frameworks = ", ".join(report.get("frameworks", [])) or "custom local patterns"
            result = f"{report['summary']} Frameworks: {frameworks}. Next: {' | '.join(report.get('recommended_next_steps', [])[:2])}"
        elif action.startswith("workspace:import:"):
            path = action.split("workspace:import:", 1)[1].strip()
            report = self.training.import_workspace(path)
            result = f"Imported {report.get('imported_lessons', 0)} lessons from {report['workspace_name']}. {report['summary']}"
        elif action.startswith("artifact:review:"):
            path = action.split("artifact:review:", 1)[1].strip()
            review = self.training.review_artifact(path)
            findings = review.get("findings", [])
            top_finding = findings[0] if findings else None
            if top_finding:
                result = (
                    f"{review['summary']} Top finding: {top_finding.get('title')} "
                    f"({top_finding.get('severity')}). Recommendation: {top_finding.get('recommendation')}"
                )
            else:
                result = review["summary"]
        elif action == "evaluation:run":
            evaluation = self.training.run_task_evaluation(persist=True)
            top_gap = next((task for task in evaluation.get("tasks", []) if task.get("status") != "ready"), None)
            result = evaluation.get("summary", "Task evaluation complete.")
            if top_gap:
                result = f"{result} Next gap: {top_gap.get('name')}: {top_gap.get('next_step')}"
        elif action.startswith("search:"):
            query = action.split("search:", 1)[1].strip()
            lessons = self.training.search_lessons(query, limit=3)
            if lessons:
                result = " | ".join(f"{lesson['title']}: {lesson['content']}" for lesson in lessons)
            else:
                result = f"No local lessons matched '{query}'."
        elif action.startswith("plan:"):
            task = action.split("plan:", 1)[1].strip()
            result = self.training.build_task_plan(task)
        elif action == "profile:status":
            profile = self.training.get_active_profile()
            result = f"Active owner profile: {profile['display_name']} ({profile['label']})" if profile else "No active owner profile."
        elif action == "training:plan":
            plan = self.training.build_training_plan()
            result = " | ".join(plan.get("next_steps", [])) or plan.get("message", "No training plan available.")
        elif action == "training:review":
            review = self.training.run_improvement_cycle(trigger="execution_router")
            top_gap = review.get("remediation_queue", [{}])[0].get("recommendation", "No open remediation items.")
            result = (
                f"Readiness {review.get('readiness_score', 0.0):.2f}. "
                f"Recent strengths: {', '.join(review.get('strengths', [])[:2]) or 'none yet'}. "
                f"Next gap: {top_gap}"
            )
        elif action == "training:remediation":
            queue = self.training.get_remediation_queue(limit=3)
            result = " | ".join(item["recommendation"] for item in queue) if queue else "No open remediation items."
        elif action.startswith("evolve:"):
            capability = action.split("evolve:", 1)[1]
            if self.meta:
                success = self.meta.evolve_new_tool(capability)
                result = f"Evolution attempt for '{capability}': {'Success' if success else 'Failed'}"
            else:
                result = "Meta-Learning engine offline."
        elif self.meta and action in self.meta.dynamic_tools:
            try:
                result = self.meta.dynamic_tools[action]("")
            except Exception as exc:
                result = f"Dynamic execution failed: {exc}"
        else:
            result = f"Attempted unknown action '{action}'. Execution failed."

        self._feed_observation_to_cache(action, result)
        return result

    def _feed_observation_to_cache(self, action_taken: str, observation: str):
        if self.cache:
            payload = {
                "type": "text",
                "source_id": "internal_execution_engine",
                "content": f"I took action '{action_taken}'. The result was: {observation}",
                "timestamp": time.time(),
            }
            self.cache.add_to_stream(payload)
            print("Action observation fed back into sensory stream.")
