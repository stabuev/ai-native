import pytest

from find_your_level import (
    BASELINE_BANKS,
    PHASES,
    SELF_ASSESSMENT,
    grade_baseline,
    route,
    self_profile,
)
from check_understanding import BANKS, compare_with_baseline, run_quiz


def _correct(bank):
    return [item["correct"] for item in bank]


def _wrong(bank):
    return [(item["correct"] + 1) % len(item["options"]) for item in bank]


def _baseline_answers(correct=True):
    chooser = _correct if correct else _wrong
    return {phase: chooser(bank) for phase, bank in BASELINE_BANKS.items()}


def test_self_profile_is_per_phase_not_one_global_score():
    answers = [0, 3, 1, 2, 0, 3, 1, 2, 0, 3, 1, 2]
    profile = self_profile(answers)
    assert profile == {phase: answer for phase, answer in enumerate(answers)}
    assert len(profile) == len(SELF_ASSESSMENT) == 12


def test_beginner_route_keeps_full_228_hours():
    result = route([0] * len(SELF_ASSESSMENT), _baseline_answers(correct=False))
    assert result["total_hours"] == 228
    assert all(item["action"] == "focus" for item in result["plan"])


def test_experienced_route_accelerates_only_with_evidence_and_never_skips():
    result = route([3] * len(SELF_ASSESSMENT), _baseline_answers(correct=True))
    plan = {item["phase"]: item for item in result["plan"]}
    assert result["total_hours"] < 228
    assert {plan[phase]["action"] for phase in (1, 4, 8)} == {"challenge"}
    assert plan[12]["action"] == "focus"
    assert all(item["action"] != "skip" for item in result["plan"])
    assert len(result["plan"]) == len(PHASES) == 13


def test_route_does_not_hide_domain_gap_behind_other_strengths():
    self_answers = [3] * len(SELF_ASSESSMENT)
    baseline = _baseline_answers(correct=True)
    baseline[1] = _wrong(BASELINE_BANKS[1])
    result = route(self_answers, baseline)
    plan = {item["phase"]: item["action"] for item in result["plan"]}
    assert plan[1] == "focus"
    assert plan[2] == "refresh"
    assert any(item["phase"] == 1 for item in result["calibration"])


def test_missing_baseline_does_not_accelerate_checkpoint_phases():
    result = route([3] * len(SELF_ASSESSMENT))
    plan = {item["phase"]: item["action"] for item in result["plan"]}
    assert plan[1] == plan[4] == plan[8] == "focus"


def test_baseline_and_exit_use_same_competency_map():
    for phase in (1, 4, 8):
        baseline = BASELINE_BANKS[phase]
        exit_bank = BANKS[phase]
        assert {item["competency"] for item in baseline} == {
            item["competency"] for item in exit_bank
        }
        assert {item["lesson"] for item in baseline} == {item["lesson"] for item in exit_bank}
        assert len(baseline) == len({item["lesson"] for item in baseline})
        for lesson in {item["lesson"] for item in exit_bank}:
            assert sum(item["lesson"] == lesson for item in exit_bank) == 2


def test_baseline_reports_competencies_and_specific_gaps():
    bank = BASELINE_BANKS[1]
    answers = _correct(bank)
    answers[0] = (answers[0] + 1) % len(bank[0]["options"])
    result = grade_baseline(1, answers)
    assert result["strong_evidence"] is False
    assert result["competency_scores"]["tokens_budget"] == 0
    assert result["gaps"][0]["lesson"] == "1.1"
    assert result["gaps"][0]["diagnosis"]


def test_exit_quiz_all_correct():
    for phase, bank in BANKS.items():
        result = run_quiz(phase, _correct(bank))
        assert result["verdict"] == "освоено"
        assert result["review_lessons"] == []
        assert result["retry_tasks"] == []


def test_exit_quiz_returns_diagnostic_feedback_and_open_retry():
    bank = BANKS[1]
    result = run_quiz(1, _wrong(bank))
    assert result["verdict"] == "нужна практика"
    assert "1.1" in result["review_lessons"]
    assert result["feedback"][0]["diagnosis"]
    assert result["feedback"][0]["correct_answer"]
    assert result["retry_tasks"][0]["prompt"]
    assert len(result["retry_tasks"][0]["criteria"]) >= 2


def test_pass_requires_coverage_of_every_lesson_not_only_total_score():
    bank = BANKS[4]
    answers = _correct(bank)
    for index, item in enumerate(bank):
        if item["lesson"] == "4.1":
            answers[index] = (item["correct"] + 1) % len(item["options"])
    result = run_quiz(4, answers)
    assert result["score"] == 0.8
    assert result["coverage_ok"] is False
    assert result["verdict"] == "нужна практика"


def test_fixed_answer_position_cannot_pass_any_exit_bank():
    for phase, bank in BANKS.items():
        for choice in range(4):
            result = run_quiz(phase, [choice] * len(bank))
            assert result["verdict"] == "нужна практика"
            assert result["score"] < 0.8


def test_progress_is_reported_by_competency():
    bank = BANKS[8]
    baseline = {item["competency"]: 0.0 for item in bank}
    result = run_quiz(8, _correct(bank), baseline=baseline)
    assert {item["delta"] for item in result["progress"]} == {1.0}
    assert {item["exit"] for item in result["progress"]} == {1.0}


def test_compare_rejects_invalid_baseline_score():
    result = run_quiz(1, _correct(BANKS[1]))
    with pytest.raises(ValueError):
        compare_with_baseline(result, {"tokens_budget": 1.5})


def test_invalid_answer_index_is_rejected():
    with pytest.raises(ValueError):
        self_profile([0] * (len(SELF_ASSESSMENT) - 1) + [4])
    with pytest.raises(ValueError):
        run_quiz(1, [0] * (len(BANKS[1]) - 1))
