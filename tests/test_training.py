from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_owner_profile_lifecycle():
    create_res = client.post(
        "/api/v1/training/profile",
        json={
            "template_id": "personal_twin",
            "display_name": "Matt Twin",
            "goals": ["Mirror my working style", "Help me make safer decisions"],
            "role_description": "Builds software, evaluates tradeoffs, and wants concise execution help.",
            "communication_style": "Direct, practical, and evidence-grounded.",
            "values": ["offline autonomy", "reversible changes"],
            "decision_principles": ["validate before acting"],
        },
    )
    assert create_res.status_code == 200
    assert create_res.json()["profile"]["label"] == "Personal Twin"

    lesson_res = client.post(
        "/api/v1/training/lesson",
        json={
            "title": "Owner decision rule",
            "content": "Prefer reversible changes, explain risk, and validate the result before calling work complete.",
            "skill_tags": ["owner_identity", "decision_judgment", "quality_standards"],
        },
    )
    assert lesson_res.status_code == 200

    profile_res = client.get("/api/v1/training/profile")
    assert profile_res.status_code == 200
    data = profile_res.json()
    assert data["profile"]["display_name"] == "Matt Twin"
    assert any(item["name"] == "owner_identity" for item in data["profile"]["competencies"])
    assert data["adaptation_model"]["model"]["template_id"] == "personal_twin"


def test_training_search_and_plan():
    search_res = client.get("/api/v1/training/lessons", params={"query": "reversible risk validate", "limit": 3})
    assert search_res.status_code == 200
    assert len(search_res.json()["lessons"]) >= 1

    plan_res = client.get("/api/v1/training/plan")
    assert plan_res.status_code == 200
    assert "next_steps" in plan_res.json()

    eval_res = client.get("/api/v1/training/evaluate")
    assert eval_res.status_code == 200
    assert "readiness_score" in eval_res.json()

    review_res = client.post("/api/v1/training/self-review")
    assert review_res.status_code == 200
    review = review_res.json()
    assert "scenario_results" in review
    assert "remediation_queue" in review


def test_workspace_analysis_and_import(tmp_path):
    workspace = tmp_path / "owner_context"
    (workspace / "notes").mkdir(parents=True)
    (workspace / "src").mkdir()
    (workspace / "config").mkdir()

    (workspace / "notes" / "working_style.md").write_text(
        "# Working style\nPurpose: keep decisions concise.\nWorkflow: inspect, decide, change, validate.\nDecision criteria: prefer reversible changes and name risks.\nFeedback: if the summary is vague, make it sharper.\n",
        encoding="utf-8",
    )
    (workspace / "src" / "helper.py").write_text(
        "def normalize(value):\n    assert value\n    return value.strip().lower()\n",
        encoding="utf-8",
    )
    (workspace / "config" / "local.json").write_text(
        "{\"purpose\": \"local owner preferences\", \"owner\": \"Matt\", \"offline\": true}\n",
        encoding="utf-8",
    )

    create_res = client.post(
        "/api/v1/training/profile",
        json={"template_id": "personal_twin", "display_name": "Repo Twin"},
    )
    assert create_res.status_code == 200

    analyze_res = client.post(
        "/api/v1/training/workspace/analyze",
        json={"path": str(workspace), "max_files": 50, "lesson_limit": 10},
    )
    assert analyze_res.status_code == 200
    report = analyze_res.json()["report"]
    assert "python" in report["frameworks"]
    assert any(artifact["kind"] == "code" for artifact in report["artifacts"])
    assert any("review_score" in artifact for artifact in report["artifacts"])

    import_res = client.post(
        "/api/v1/training/workspace/import",
        json={"path": str(workspace), "max_files": 50, "lesson_limit": 10},
    )
    assert import_res.status_code == 200
    imported_report = import_res.json()["report"]
    assert imported_report["imported_lessons"] >= 2

    second_import_res = client.post(
        "/api/v1/training/workspace/import",
        json={"path": str(workspace), "max_files": 50, "lesson_limit": 10},
    )
    assert second_import_res.status_code == 200
    assert second_import_res.json()["report"]["imported_lessons"] == 0

    profile_res = client.get("/api/v1/training/profile")
    assert profile_res.status_code == 200
    profile_data = profile_res.json()
    assert profile_data["workspace"]["workspace_name"] == "owner_context"
    assert profile_data["evaluation"]["readiness_score"] > 0.0
    assert "self_review" in profile_data
    assert "task_evaluation" in profile_data
    assert "artifact_reviews" in profile_data
    assert "remediation_queue" in profile_data

    artifact_res = client.post(
        "/api/v1/training/artifact/review",
        json={"path": "notes/working_style.md"},
    )
    assert artifact_res.status_code == 200
    artifact_review = artifact_res.json()["review"]
    assert artifact_review["artifact_type"] == "document"
    assert artifact_review["score"] > 0

    task_eval_res = client.post("/api/v1/training/evals/run")
    assert task_eval_res.status_code == 200
    task_evaluation = task_eval_res.json()["evaluation"]
    assert task_evaluation["overall_score"] > 0
    assert any(task["name"] == "Owner Identity Model" for task in task_evaluation["tasks"])


def test_training_records_interactions_and_surfaces_review():
    create_res = client.post(
        "/api/v1/training/profile",
        json={"template_id": "personal_twin", "display_name": "Interaction Twin"},
    )
    assert create_res.status_code == 200

    client.post(
        "/api/v1/training/lesson",
        json={
            "title": "Correction style",
            "content": "When feedback says the answer is vague, make the next response concrete and decision-first.",
            "skill_tags": ["feedback_adaptation", "communication_style", "owner_identity"],
        },
    )

    review_before = client.post("/api/v1/training/self-review")
    assert review_before.status_code == 200

    from src.training.service import TrainingService

    service = TrainingService()
    service.record_interaction(
        query="Make this clearer and more direct.",
        response="I will make the next answer concrete and decision-first.",
        context_blocks=["Correction style: make the next response concrete..."],
        process_used="System 2",
        action_result="Captured owner correction.",
    )

    review_after = client.post("/api/v1/training/self-review")
    assert review_after.status_code == 200
    review = review_after.json()
    assert review["recent_interaction_count"] >= 1
    assert isinstance(review["generated_reflections"], list)
