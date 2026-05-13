from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.training.service import TrainingService


router = APIRouter()
training = TrainingService()


class ProfilePayload(BaseModel):
    template_id: str = "personal_twin"
    display_name: str | None = None
    goals: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    owner_name: str | None = None
    role_description: str | None = None
    communication_style: str | None = None
    values: list[str] = Field(default_factory=list)
    decision_principles: list[str] = Field(default_factory=list)


class LessonPayload(BaseModel):
    title: str
    content: str
    skill_tags: list[str] = Field(default_factory=list)
    lesson_type: str = "principle"
    source_id: str = "manual"


class WorkspacePayload(BaseModel):
    path: str
    max_files: int = 200
    lesson_limit: int = 20


class ArtifactPayload(BaseModel):
    path: str


@router.get("/templates")
async def list_training_templates():
    return {"templates": training.list_templates()}


@router.get("/profile")
async def get_profile():
    profile = training.get_active_profile()
    plan = training.build_training_plan()
    evaluation = training.evaluate_readiness(persist=False) if profile else {"status": "unconfigured", "readiness_score": 0.0, "gaps": []}
    self_review = training.get_latest_self_review()
    return {
        "profile": profile,
        "plan": plan,
        "evaluation": evaluation,
        "workspace": training.get_latest_workspace_snapshot(),
        "self_review": self_review,
        "task_evaluation": training.get_latest_task_evaluation(),
        "artifact_reviews": training.get_recent_artifact_reviews(limit=5),
        "adaptation_model": training.get_adaptation_model_definition(),
        "remediation_queue": training.get_remediation_queue(),
    }


@router.post("/profile")
async def activate_profile(payload: ProfilePayload):
    profile = training.activate_profile(
        template_id=payload.template_id,
        display_name=payload.display_name,
        goals=payload.goals,
        constraints=payload.constraints,
        owner_name=payload.owner_name,
        role_description=payload.role_description,
        communication_style=payload.communication_style,
        values=payload.values,
        decision_principles=payload.decision_principles,
    )
    return {"status": "success", "profile": profile}


@router.post("/lesson")
async def add_lesson(payload: LessonPayload):
    lesson = training.add_lesson(
        title=payload.title,
        content=payload.content,
        skill_tags=payload.skill_tags,
        lesson_type=payload.lesson_type,
        source_id=payload.source_id,
    )
    return {"status": "success", "lesson": lesson}


@router.get("/lessons")
async def search_lessons(query: str, limit: int = 5):
    return {"lessons": training.search_lessons(query, limit=limit)}


@router.get("/plan")
async def get_plan():
    return training.build_training_plan()


@router.get("/evaluate")
async def evaluate_training():
    return training.evaluate_readiness()


@router.get("/self-review")
async def get_self_review():
    review = training.get_latest_self_review()
    if review:
        return review
    if training.get_active_profile():
        return training.run_self_review(trigger="api_read", persist=False, generate_reflections=False)
    return {"status": "unconfigured", "readiness_score": 0.0, "gaps": ["No active owner profile."]}


@router.post("/self-review")
async def run_self_review():
    return training.run_improvement_cycle(trigger="manual_api")


@router.get("/remediation")
async def get_remediation_queue():
    return {"items": training.get_remediation_queue()}


@router.get("/adaptation-model")
async def get_adaptation_model():
    return training.get_adaptation_model_definition()


@router.post("/artifact/review")
async def review_artifact(payload: ArtifactPayload):
    return {"status": "success", "review": training.review_artifact(payload.path)}


@router.get("/artifact/reviews")
async def get_artifact_reviews(limit: int = 20):
    return {"reviews": training.get_recent_artifact_reviews(limit=limit)}


@router.post("/evals/run")
async def run_task_evaluation():
    return {"status": "success", "evaluation": training.run_task_evaluation(persist=True)}


@router.get("/evals/latest")
async def get_latest_task_evaluation():
    evaluation = training.get_latest_task_evaluation()
    if evaluation:
        return evaluation
    return {"status": "unconfigured", "overall_score": 0.0, "tasks": []}


@router.get("/export")
async def export_training_snapshot():
    return training.export_snapshot()


@router.post("/workspace/analyze")
async def analyze_workspace(payload: WorkspacePayload):
    report = training.analyze_workspace(payload.path, max_files=payload.max_files)
    return {"status": "success", "report": report}


@router.post("/workspace/import")
async def import_workspace(payload: WorkspacePayload):
    report = training.import_workspace(
        workspace_path=payload.path,
        max_files=payload.max_files,
        lesson_limit=payload.lesson_limit,
    )
    return {"status": "success", "report": report}
