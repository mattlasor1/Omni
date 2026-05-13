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

    import_res = client.post(
        "/api/v1/training/workspace/import",
        json={"path": str(workspace), "max_files": 50, "lesson_limit": 10},
    )
    assert import_res.status_code == 200
    imported_report = import_res.json()["report"]
    assert imported_report["imported_lessons"] >= 2

    profile_res = client.get("/api/v1/training/profile")
    assert profile_res.status_code == 200
    profile_data = profile_res.json()
    assert profile_data["workspace"]["workspace_name"] == "analytics_repo"
    assert profile_data["evaluation"]["readiness_score"] > 0.0
