from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.training.service import TrainingService


router = APIRouter()
training = TrainingService()


class ProfilePayload(BaseModel):
    template_id: str = "generic_professional"
    display_name: str | None = None
    goals: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


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


@router.get("/templates")
async def list_training_templates():
    return {"templates": training.list_templates()}


@router.get("/profile")
async def get_profile():
    profile = training.get_active_profile()
    plan = training.build_training_plan()
    evaluation = training.evaluate_readiness(persist=False) if profile else {"status": "unconfigured", "readiness_score": 0.0, "gaps": []}
    return {"profile": profile, "plan": plan, "evaluation": evaluation, "workspace": training.get_latest_workspace_snapshot()}


@router.post("/profile")
async def activate_profile(payload: ProfilePayload):
    profile = training.activate_profile(
        template_id=payload.template_id,
        display_name=payload.display_name,
        goals=payload.goals,
        constraints=payload.constraints,
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
