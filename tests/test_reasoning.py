from types import SimpleNamespace

from src.learning.reasoning import CognitiveReasoningEngine


class FakePipeline:
    def __init__(self):
        self.tokenizer = SimpleNamespace(eos_token_id=0)

    def __call__(self, prompt, **kwargs):
        assert isinstance(prompt, str)
        return [{"generated_text": "grounded local answer"}]


def test_reasoning_uses_string_prompt_with_pipeline():
    engine = CognitiveReasoningEngine.__new__(CognitiveReasoningEngine)
    engine.client = FakePipeline()

    result = engine._generate_generic(
        system_prompt="You are helpful.",
        user_prompt="Answer the question.",
        max_tokens=50,
        temperature=0.3,
    )

    assert result == "grounded local answer"


def test_reasoning_heuristic_response_when_offline():
    engine = CognitiveReasoningEngine.__new__(CognitiveReasoningEngine)
    engine.client = None

    result = engine.generate_response(
        "How do I debug a pipeline?",
        ["Check lineage first.", "Inspect retries and recent deploys."],
    )

    assert "Check lineage first." in result
    assert "Query handled offline" in result
