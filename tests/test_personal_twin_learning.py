from src.training.personal_twin import PersonalTwinLearningPack


def test_document_review_flags_missing_owner_model_signals(tmp_path):
    note = tmp_path / "decision.md"
    note.write_text("Use the faster option next time.\n", encoding="utf-8")

    review = PersonalTwinLearningPack().review_artifact(note)

    assert review["artifact_type"] == "document"
    assert review["score"] < 100
    assert any("purpose" in finding["title"].lower() for finding in review["findings"])
    assert any("validation" in finding["title"].lower() for finding in review["findings"])


def test_code_review_flags_external_dependency_and_missing_validation(tmp_path):
    script = tmp_path / "assistant_helper.py"
    script.write_text(
        "def fetch_context():\n    return 'https://example.com/context'\n\ndef transform(value):\n    return value.strip()\n",
        encoding="utf-8",
    )

    review = PersonalTwinLearningPack().review_artifact(script)

    assert review["artifact_type"] == "code"
    assert any(finding["title"] == "External connectivity signal" for finding in review["findings"])
    assert any(finding["title"] == "Behavior lacks validation evidence" for finding in review["findings"])


def test_workspace_evaluation_scores_owner_model_tasks(tmp_path):
    workspace = tmp_path / "owner_context"
    (workspace / "notes").mkdir(parents=True)
    (workspace / "src").mkdir()
    (workspace / "notes" / "style.md").write_text(
        "# Working style\nPurpose: be concise.\nWorkflow: inspect, decide, validate.\nDecision criteria: prefer reversible changes.\nFeedback: correct summaries quickly.\n",
        encoding="utf-8",
    )
    (workspace / "src" / "helper.py").write_text(
        "def transform(value):\n    assert value\n    return value.strip()\n",
        encoding="utf-8",
    )
    snapshot = {
        "workspace_path": str(workspace),
        "artifacts": [
            {
                "path": "notes/style.md",
                "kind": "document",
                "summary": "Owner style and workflow note.",
                "skill_tags": ["owner_identity", "workflow_fluency", "decision_judgment", "feedback_adaptation"],
                "signals": ["Describes repeatable work or procedure."],
            },
            {
                "path": "src/helper.py",
                "kind": "code",
                "summary": "Local helper with validation.",
                "skill_tags": ["artifact_fluency", "quality_standards"],
                "signals": ["Contains validation or success signals."],
            },
        ],
    }
    profile = {
        "goals": ["Mirror my working style"],
        "constraints": ["Stay offline"],
        "role_description": "Owner-defined work context",
        "values": ["Reversible changes"],
        "decision_principles": ["Validate before acting"],
    }
    lessons = [
        {
            "title": "Tone preference",
            "content": "I prefer concise answers with the decision first.",
            "lesson_type": "preference",
            "skill_tags": ["owner_identity", "communication_style"],
        }
    ]
    interactions = [{"id": "1", "query": "Prefer shorter summaries", "response": "Understood", "action_result": ""}]

    evaluation = PersonalTwinLearningPack().evaluate_workspace(snapshot, profile=profile, lessons=lessons, interactions=interactions)

    assert evaluation["overall_score"] > 0
    assert {task["name"] for task in evaluation["tasks"]} == {
        "Owner Identity Model",
        "Domain Understanding",
        "Workflow Fluency",
        "Decision Judgment",
        "Feedback Adaptation",
    }
