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
