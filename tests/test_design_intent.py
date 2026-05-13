from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_offline_profession_twin_acceptance_flow(tmp_path):
    workspace = tmp_path / "analytics_repo"
    (workspace / "models").mkdir(parents=True)
    (workspace / "dags").mkdir()
    (workspace / "runbooks").mkdir()
    (workspace / "dbt_project.yml").write_text(
        "name: analytics_project\nmodels:\n  analytics:\n    +materialized: incremental\n",
        encoding="utf-8",
    )
    (workspace / "models" / "orders.sql").write_text(
        "select customer_id, order_date, sum(amount) as revenue from raw.orders group by 1,2\n",
        encoding="utf-8",
    )
    (workspace / "dags" / "daily_load.py").write_text(
        "from airflow import DAG\nfrom airflow.operators.python import PythonOperator\n",
        encoding="utf-8",
    )
    (workspace / "runbooks" / "incident.md").write_text(
        "# Incident runbook\nRollback, inspect the watermark, and verify idempotent backfill before retrying.\n",
        encoding="utf-8",
    )

    profile_res = client.post(
        "/api/v1/training/profile",
        json={
            "template_id": "data_engineer",
            "display_name": "Acceptance Twin",
            "goals": ["Review SQL models", "Recover failed DAGs"],
        },
    )
    assert profile_res.status_code == 200

    import_res = client.post(
        "/api/v1/training/workspace/import",
        json={"path": str(workspace), "max_files": 50, "lesson_limit": 10},
    )
    assert import_res.status_code == 200
    assert import_res.json()["report"]["imported_lessons"] >= 4

    artifact_res = client.post(
        "/api/v1/training/artifact/review",
        json={"path": "models/orders.sql"},
    )
    assert artifact_res.status_code == 200
    assert artifact_res.json()["review"]["artifact_type"] == "sql_model"

    task_eval_res = client.post("/api/v1/training/evals/run")
    assert task_eval_res.status_code == 200
    task_evaluation = task_eval_res.json()["evaluation"]
    assert task_evaluation["overall_score"] > 0
    assert any(task["status"] in {"ready", "needs_work"} for task in task_evaluation["tasks"])

    query_res = client.post(
        "/api/v1/query",
        json={
            "query": "Review the SQL model and recover the failed DAG",
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
