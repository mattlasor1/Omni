from src.training.data_engineer import DataEngineerSkillPack


def test_sql_review_flags_select_star_and_join_risk(tmp_path):
    model = tmp_path / "orders.sql"
    model.write_text(
        "select * from raw.orders o join raw.customers c on o.customer_id = c.customer_id\n",
        encoding="utf-8",
    )

    review = DataEngineerSkillPack().review_artifact(model)

    assert review["artifact_type"] == "sql_model"
    assert review["score"] < 100
    assert any(finding["title"] == "Avoid select star" for finding in review["findings"])
    assert any("relationship" in suggestion.lower() for suggestion in review["suggested_tests"])


def test_airflow_review_flags_missing_recovery_policy(tmp_path):
    dag = tmp_path / "daily_load.py"
    dag.write_text(
        "from airflow import DAG\nfrom airflow.operators.python import PythonOperator\n",
        encoding="utf-8",
    )

    review = DataEngineerSkillPack().review_artifact(dag)

    assert review["artifact_type"] == "airflow_dag"
    assert any(finding["title"] == "Retries are not explicit" for finding in review["findings"])
    assert any(finding["title"] == "Failure callback missing" for finding in review["findings"])


def test_workspace_evaluation_scores_all_data_engineering_tasks(tmp_path):
    workspace = tmp_path / "analytics_repo"
    (workspace / "models").mkdir(parents=True)
    (workspace / "dags").mkdir()
    (workspace / "runbooks").mkdir()
    (workspace / "models" / "orders.sql").write_text(
        "select customer_id, sum(amount) as revenue from raw.orders group by 1\n",
        encoding="utf-8",
    )
    (workspace / "schema.yml").write_text(
        "models:\n  - name: orders\n    columns:\n      - name: customer_id\n        tests:\n          - not_null\n",
        encoding="utf-8",
    )
    (workspace / "dags" / "daily_load.py").write_text(
        "from airflow import DAG\nwith DAG('daily', schedule='@daily', catchup=False, default_args={'retries': 2}) as dag:\n    pass\n",
        encoding="utf-8",
    )
    (workspace / "runbooks" / "incident.md").write_text(
        "# Incident\nRollback the load, inspect logs, validate row counts, and escalate to owner.\n",
        encoding="utf-8",
    )
    snapshot = {
        "workspace_path": str(workspace),
        "artifacts": [
            {"path": "models/orders.sql", "kind": "sql_model"},
            {"path": "schema.yml", "kind": "config"},
            {"path": "dags/daily_load.py", "kind": "python_job"},
            {"path": "runbooks/incident.md", "kind": "document"},
        ],
    }

    evaluation = DataEngineerSkillPack().evaluate_workspace(snapshot)

    assert evaluation["overall_score"] > 0
    assert {task["name"] for task in evaluation["tasks"]} == {
        "SQL Model Review",
        "dbt Quality Coverage",
        "Airflow Recovery",
        "Operator Runbook",
    }
