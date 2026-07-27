import pytest

from eval_harness import (
    DEMO_CASES,
    DEMO_OUTPUTS,
    compare_versions,
    evaluate,
    exact_label,
    naive_contains,
    recorded_runner,
    release_decision,
    validate_cases,
)


def test_exact_label_normalizes_but_contains_can_lie():
    assert exact_label(" ACCESS ", "access") == 1.0
    assert exact_label("billing, not access", "access") == 0.0
    assert naive_contains("billing, not access", "access") == 1.0


def test_invalid_or_duplicate_cases_fail_before_the_run():
    with pytest.raises(ValueError, match="non-empty"):
        validate_cases([])

    duplicate = [DEMO_CASES[0], dict(DEMO_CASES[0])]
    with pytest.raises(ValueError, match="duplicate"):
        validate_cases(duplicate)


def test_evaluate_preserves_case_and_slice_evidence():
    report = evaluate("baseline", DEMO_CASES, recorded_runner)

    assert report["score"] == pytest.approx(0.6)
    assert report["passed"] == 3
    assert report["total"] == 5
    assert report["by_slice"]["critical"] == {
        "score": 1.0,
        "passed": 2,
        "total": 2,
    }
    assert report["per_case"][0]["id"] == "billing-double-charge"


def test_overall_improvement_can_hide_a_critical_regression():
    comparison = compare_versions(
        "baseline",
        "candidate",
        DEMO_CASES,
        recorded_runner,
    )

    assert comparison["delta"] == pytest.approx(0.2)
    assert comparison["slice_deltas"]["critical"] == pytest.approx(-0.5)
    assert comparison["regressions"] == ["access-after-payment"]
    assert set(comparison["improvements"]) == {
        "billing-double-charge",
        "billing-after-cancellation",
    }

    decision = release_decision(comparison, protected_slices=("critical",))
    assert decision["decision"] == "reject"
    assert "critical" in decision["reasons"][0]


def test_candidate_without_regressions_can_be_accepted():
    safe_outputs = {
        **DEMO_OUTPUTS,
        "safe-candidate": {
            **DEMO_OUTPUTS["candidate"],
            "access-after-payment": "access",
        },
    }

    def run_safe(version, case):
        return safe_outputs[version][case["id"]]

    comparison = compare_versions(
        "baseline",
        "safe-candidate",
        DEMO_CASES,
        run_safe,
    )
    decision = release_decision(comparison, protected_slices=("critical",))

    assert comparison["delta"] == pytest.approx(0.4)
    assert comparison["regressions"] == []
    assert decision["decision"] == "accept"


def test_missing_protected_slice_requires_review():
    comparison = compare_versions(
        "baseline",
        "candidate",
        DEMO_CASES,
        recorded_runner,
    )
    decision = release_decision(comparison, protected_slices=("privacy",))

    assert decision["decision"] == "review"
    assert "no cases" in decision["reasons"][0]


def test_known_regression_outweighs_a_missing_protected_slice():
    comparison = compare_versions(
        "baseline",
        "candidate",
        DEMO_CASES,
        recorded_runner,
    )
    decision = release_decision(
        comparison,
        protected_slices=("critical", "privacy"),
    )

    assert decision["decision"] == "reject"
    assert any("critical" in reason for reason in decision["reasons"])
    assert any("privacy" in reason for reason in decision["reasons"])


def test_unprotected_case_regression_requires_review():
    review_outputs = {
        **DEMO_OUTPUTS,
        "review-candidate": {
            **DEMO_OUTPUTS["candidate"],
            "bug-empty-export": "other",
            "access-after-payment": "access",
        },
    }

    def run_review(version, case):
        return review_outputs[version][case["id"]]

    comparison = compare_versions(
        "baseline",
        "review-candidate",
        DEMO_CASES,
        run_review,
    )
    decision = release_decision(comparison, protected_slices=("critical",))

    assert comparison["delta"] == pytest.approx(0.2)
    assert comparison["regressions"] == ["bug-empty-export"]
    assert decision["decision"] == "review"


def test_invalid_or_broken_grader_fails_with_case_context():
    with pytest.raises(ValueError, match="billing-double-charge"):
        evaluate(
            "candidate",
            DEMO_CASES,
            recorded_runner,
            grader=lambda pred, expected: float("nan"),
        )

    def broken_grader(pred, expected):
        raise LookupError("rubric unavailable")

    with pytest.raises(
        RuntimeError,
        match="grader failed for candidate/billing-double-charge",
    ):
        evaluate("candidate", DEMO_CASES, recorded_runner, grader=broken_grader)


def test_runner_failure_is_not_silently_counted_as_bad_quality():
    def broken_runner(version, case):
        raise TimeoutError("provider timeout")

    with pytest.raises(RuntimeError, match="runner failed"):
        evaluate("candidate", DEMO_CASES, broken_runner)
