from src.execution.authority import TrustAndAuthorityProtocol


def test_safe_local_actions_bypass_authority_queue():
    authority = TrustAndAuthorityProtocol()

    allowed = authority.evaluate_authority(
        {"score": 0.1, "action": {"action": "plan:Review the owner decision note"}},
        avg_bayesian_belief=0.1,
    )

    assert allowed is True


def test_owner_model_actions_bypass_authority_queue():
    authority = TrustAndAuthorityProtocol()

    assert authority.evaluate_authority(
        {"score": 0.1, "action": {"action": "artifact:review:notes/decision.md"}},
        avg_bayesian_belief=0.1,
    ) is True
    assert authority.evaluate_authority(
        {"score": 0.1, "action": {"action": "evaluation:run"}},
        avg_bayesian_belief=0.1,
    ) is True


def test_risky_unknown_action_still_requires_authority():
    authority = TrustAndAuthorityProtocol()

    allowed = authority.evaluate_authority(
        {"score": 0.1, "action": {"action": "filesystem:mutate:/tmp"}},
        avg_bayesian_belief=0.1,
    )

    assert allowed is False
