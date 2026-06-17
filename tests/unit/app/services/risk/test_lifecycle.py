import pytest
from app.services.risk.lifecycle import LifecycleService, normalize_lifecycle_state
from app.utils.errors import ValidationError


def test_lifecycle_state_normalization():
    # Canonical states
    assert normalize_lifecycle_state("research") == "research"
    assert normalize_lifecycle_state("validated") == "validated"

    # Aliases
    assert normalize_lifecycle_state("draft") == "research"
    assert normalize_lifecycle_state("backtested") == "validated"
    assert normalize_lifecycle_state("paper") == "paper_active"
    assert normalize_lifecycle_state("approved_for_live") == "live_candidate"
    assert normalize_lifecycle_state("live") == "live_active"

    # Unrecognized raises ValidationError
    with pytest.raises(ValidationError):
        normalize_lifecycle_state("arbitrary_unknown_state")


def test_lifecycle_transitions():
    # Research -> Validated transition is allowed
    res = LifecycleService.transition("strat_1", "research", "validated")
    assert res["status"] == "success"
    assert res["new_state"] == "validated"

    # Validated -> research is not allowed
    with pytest.raises(ValidationError):
        LifecycleService.transition("strat_1", "validated", "research")

    # Paper Active -> Live Candidate requires board approval and review evidence
    with pytest.raises(ValidationError):
        LifecycleService.transition(
            "strat_1", "paper_active", "live_candidate", board_approved=False
        )

    with pytest.raises(ValidationError):
        LifecycleService.transition(
            "strat_1",
            "paper_active",
            "live_candidate",
            board_approved=True,
            review_evidence=None,
        )

    evidence = {"win_rate": 0.55, "profit_factor": 1.5}
    res2 = LifecycleService.transition(
        "strat_1",
        "paper_active",
        "live_candidate",
        board_approved=True,
        review_evidence=evidence,
    )
    assert res2["status"] == "success"
    assert res2["new_state"] == "live_candidate"
