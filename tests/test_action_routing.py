from types import SimpleNamespace

from src.generation.action import ProceduralActionEngine


def test_artifact_review_routes_to_owner_model_action():
    engine = ProceduralActionEngine(SimpleNamespace(client=None))

    action = engine.decide_action("review notes/decision.md", [])

    assert action["action"] == "artifact:review:notes/decision.md"


def test_task_evaluation_routes_to_local_eval_action():
    engine = ProceduralActionEngine(SimpleNamespace(client=None))

    action = engine.decide_action("run task evaluation", [])

    assert action["action"] == "evaluation:run"
