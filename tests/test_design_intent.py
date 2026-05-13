from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_offline_personal_twin_acceptance_flow(tmp_path):
    workspace = tmp_path / "owner_context"
    (workspace / "notes").mkdir(parents=True)
    (workspace / "src").mkdir()
    (workspace / "notes" / "decision_style.md").write_text(
        "# Decision style\nPurpose: decide with reversible changes first.\nWorkflow: inspect evidence, state risk, change, validate.\nDecision criteria: prefer local evidence and small steps.\nFeedback: be concise and correct mistakes quickly.\n",
        encoding="utf-8",
    )
    (workspace / "src" / "daily_helper.py").write_text(
        "def summarize(items):\n    assert items\n    return ', '.join(items[:3])\n",
        encoding="utf-8",
    )

    profile_res = client.post(
        "/api/v1/training/profile",
        json={
            "template_id": "personal_twin",
            "display_name": "Acceptance Twin",
            "goals": ["Mirror my reasoning style", "Help with day-to-day decisions"],
            "communication_style": "Concise, direct, and grounded in local evidence.",
            "decision_principles": ["Prefer reversible local changes"],
        },
    )
    assert profile_res.status_code == 200

    import_res = client.post(
        "/api/v1/training/workspace/import",
        json={"path": str(workspace), "max_files": 50, "lesson_limit": 10},
    )
    assert import_res.status_code == 200
    assert import_res.json()["report"]["imported_lessons"] >= 2

    artifact_res = client.post(
        "/api/v1/training/artifact/review",
        json={"path": "notes/decision_style.md"},
    )
    assert artifact_res.status_code == 200
    assert artifact_res.json()["review"]["artifact_type"] == "document"

    task_eval_res = client.post("/api/v1/training/evals/run")
    assert task_eval_res.status_code == 200
    task_evaluation = task_eval_res.json()["evaluation"]
    assert task_evaluation["overall_score"] > 0
    assert any(task["name"] == "Owner Identity Model" for task in task_evaluation["tasks"])

    query_res = client.post(
        "/api/v1/query",
        json={
            "query": "Use my decision style to plan a small reversible change",
            "execute_action": True,
        },
    )
    assert query_res.status_code == 200
    query = query_res.json()
    assert query["action_decided"]["action"].startswith("plan:")
    assert "Confidence below threshold" not in query["action_result"]
    assert query["training_profile"]["display_name"] == "Acceptance Twin"

    review_res = client.post("/api/v1/training/self-review")
    assert review_res.status_code == 200
    review = review_res.json()
    assert review["readiness_score"] > 0
    assert review["recent_interaction_count"] >= 1
    assert "remediation_queue" in review

    state_res = client.get("/api/v1/state")
    assert state_res.status_code == 200
    state = state_res.json()
    assert "review" in state["maintenance"]["tasks"]
    assert state["training"]["self_review"]["status"] in {"ready", "training"}
