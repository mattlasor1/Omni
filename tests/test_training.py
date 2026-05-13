from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_training_profile_lifecycle():
    create_res = client.post(
        "/api/v1/training/profile",
        json={
            "template_id": "data_engineer",
            "display_name": "Warehouse Twin",
            "goals": ["Help with SQL reviews", "Improve pipeline runbooks"],
        },
    )
    assert create_res.status_code == 200
    assert create_res.json()["profile"]["label"] == "Data Engineer"

    lesson_res = client.post(
        "/api/v1/training/lesson",
        json={
            "title": "Incremental dbt rule",
            "content": "Prefer partition pruning and idempotent merge logic for large fact models.",
            "skill_tags": ["sql_modeling", "performance"],
        },
    )
    assert lesson_res.status_code == 200

    profile_res = client.get("/api/v1/training/profile")
    assert profile_res.status_code == 200
    data = profile_res.json()
    assert data["profile"]["display_name"] == "Warehouse Twin"
    assert any(item["name"] == "sql_modeling" for item in data["profile"]["competencies"])


def test_training_search_and_plan():
    search_res = client.get("/api/v1/training/lessons", params={"query": "partition pruning merge", "limit": 3})
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
    workspace = tmp_path / "analytics_repo"
    (workspace / "models").mkdir(parents=True)
    (workspace / "dags").mkdir()
    (workspace / "runbooks").mkdir()

    (workspace / "dbt_project.yml").write_text("name: analytics_project\nmodels:\n  analytics:\n    +materialized: table\n", encoding="utf-8")
    (workspace / "models" / "orders.sql").write_text(
        "select customer_id, sum(amount) as revenue from raw.orders group by 1\n",
        encoding="utf-8",
    )
    (workspace / "dags" / "daily_load.py").write_text(
        "from airflow import DAG\nfrom airflow.operators.python import PythonOperator\n",
        encoding="utf-8",
    )
    (workspace / "runbooks" / "incident.md").write_text(
        "# Warehouse incident runbook\nRollback failed load and inspect retry logs.\n",
        encoding="utf-8",
    )

    create_res = client.post(
        "/api/v1/training/profile",
        json={"template_id": "data_engineer", "display_name": "Repo Twin"},
    )
    assert create_res.status_code == 200

    analyze_res = client.post(
        "/api/v1/training/workspace/analyze",
        json={"path": str(workspace), "max_files": 50, "lesson_limit": 10},
    )
    assert analyze_res.status_code == 200
    report = analyze_res.json()["report"]
    assert "dbt" in report["frameworks"]
    assert any(artifact["kind"] == "python_job" for artifact in report["artifacts"])
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
    assert profile_data["workspace"]["workspace_name"] == "analytics_repo"
    assert profile_data["evaluation"]["readiness_score"] > 0.0
    assert "self_review" in profile_data
    assert "task_evaluation" in profile_data
    assert "artifact_reviews" in profile_data
    assert "remediation_queue" in profile_data

    artifact_res = client.post(
        "/api/v1/training/artifact/review",
        json={"path": "models/orders.sql"},
    )
    assert artifact_res.status_code == 200
    artifact_review = artifact_res.json()["review"]
    assert artifact_review["artifact_type"] == "sql_model"
    assert artifact_review["score"] > 0

    task_eval_res = client.post("/api/v1/training/evals/run")
    assert task_eval_res.status_code == 200
    task_evaluation = task_eval_res.json()["evaluation"]
    assert task_evaluation["overall_score"] > 0
    assert any(task["name"] == "SQL Model Review" for task in task_evaluation["tasks"])


def test_training_records_interactions_and_surfaces_review():
    create_res = client.post(
        "/api/v1/training/profile",
        json={"template_id": "data_engineer", "display_name": "Interaction Twin"},
    )
    assert create_res.status_code == 200

    client.post(
        "/api/v1/training/lesson",
        json={
            "title": "DAG rollback rule",
            "content": "Inspect the failing task logs, preserve the watermark, and only backfill after confirming idempotency.",
            "skill_tags": ["orchestration", "incident_response"],
        },
    )

    review_before = client.post("/api/v1/training/self-review")
    assert review_before.status_code == 200

    from src.training.service import TrainingService

    service = TrainingService()
    service.record_interaction(
        query="How do I recover a failed DAG run?",
        response="Inspect task logs, verify retry safety, and backfill only after idempotency checks.",
        context_blocks=["DAG rollback rule: Inspect the failing task logs..."],
        process_used="System 2",
        action_result="Generated local recovery plan.",
    )

    review_after = client.post("/api/v1/training/self-review")
    assert review_after.status_code == 200
    review = review_after.json()
    assert review["recent_interaction_count"] >= 1
    assert isinstance(review["generated_reflections"], list)
