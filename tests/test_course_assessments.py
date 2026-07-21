import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


find_your_level = _load_module(
    "find_your_level",
    ".claude/skills/find-your-level/find_your_level.py",
)
check_understanding = _load_module(
    "check_understanding",
    ".claude/skills/check-understanding/check_understanding.py",
)

BASELINE_BANKS = find_your_level.BASELINE_BANKS
PHASES = find_your_level.PHASES
SELF_ASSESSMENT = find_your_level.SELF_ASSESSMENT
BANKS = check_understanding.BANKS


def _correct(bank):
    return [item["correct"] for item in bank]


def _wrong(bank):
    return [(item["correct"] + 1) % len(item["options"]) for item in bank]


def _baseline_answers(correct=True):
    chooser = _correct if correct else _wrong
    return {phase: chooser(bank) for phase, bank in BASELINE_BANKS.items()}


def test_self_profile_is_per_phase_not_one_global_score():
    answers = [0, 3, 1, 2, 0, 3, 1, 2, 0, 3, 1, 2]
    profile = find_your_level.self_profile(answers)
    assert profile == {phase: answer for phase, answer in enumerate(answers)}
    assert len(profile) == len(SELF_ASSESSMENT) == 12


def test_baseline_is_suggested_only_for_claimed_experience():
    answers = [0] * len(SELF_ASSESSMENT)
    answers[1] = 2
    answers[4] = 3
    answers[8] = 1
    assert find_your_level.suggested_baseline_phases(answers) == [1, 4]


def test_beginner_route_keeps_every_phase_in_focus_and_uses_ranges():
    result = find_your_level.route([0] * len(SELF_ASSESSMENT))
    assert all(item["action"] == "focus" for item in result["plan"])
    assert len(result["plan"]) == len(PHASES) == 13
    low, high = result["total_hours_range"]
    assert low < 228 < high
    assert "total_hours" not in result


def test_experienced_route_accelerates_only_with_evidence_and_never_skips():
    result = find_your_level.route(
        [3] * len(SELF_ASSESSMENT),
        _baseline_answers(correct=True),
    )
    plan = {item["phase"]: item for item in result["plan"]}
    assert {plan[phase]["action"] for phase in (1, 4, 8)} == {"challenge"}
    assert plan[12]["action"] == "focus"
    assert all(item["action"] != "skip" for item in result["plan"])
    assert result["total_hours_range"][1] < 228


def test_self_assessment_without_scenarios_cannot_assign_challenge():
    result = find_your_level.route([3] * len(SELF_ASSESSMENT))
    plan = {item["phase"]: item["action"] for item in result["plan"]}
    assert plan[1] == plan[4] == plan[8] == "refresh"
    assert "challenge" not in plan.values()


def test_route_does_not_hide_domain_gap_behind_other_strengths():
    self_answers = [3] * len(SELF_ASSESSMENT)
    baseline = _baseline_answers(correct=True)
    baseline[1] = _wrong(BASELINE_BANKS[1])
    result = find_your_level.route(self_answers, baseline)
    plan = {item["phase"]: item["action"] for item in result["plan"]}
    assert plan[1] == "focus"
    assert plan[2] == "refresh"
    assert any(item["phase"] == 1 for item in result["calibration"])


def test_route_markdown_uses_ranges_and_challenge_warning():
    result = find_your_level.route([0] * len(SELF_ASSESSMENT))
    markdown = find_your_level.render_route_markdown(
        result,
        "Codex",
        "/work/ai-native",
        "Проверить изменение в репозитории",
        "Все тесты проходят",
        "рабочий кандидат",
    )
    assert "**Ориентир:**" in markdown
    assert "167.5" not in markdown
    assert "автоматический пропуск" in markdown
    assert "Codex" in markdown
    assert "**Сквозная задача из 0.1:** Проверить изменение в репозитории" in markdown
    assert "**Критерий успеха:** Все тесты проходят" in markdown
    assert "**Роль агента:** рабочий кандидат" in markdown


def test_route_markdown_keeps_baseline_for_later_exit_check():
    result = find_your_level.route(
        [3] * len(SELF_ASSESSMENT),
        {1: _correct(BASELINE_BANKS[1])},
    )
    markdown = find_your_level.render_route_markdown(result)
    assert "### baseline_competencies" in markdown
    assert '"tokens_budget": 1.0' in markdown


def test_baseline_and_exit_use_same_competency_map():
    for phase in (1, 4, 8):
        baseline = BASELINE_BANKS[phase]
        exit_bank = BANKS[phase]
        assert {item["competency"] for item in baseline} == {
            item["competency"] for item in exit_bank
        }
        assert {item["lesson"] for item in baseline} == {
            item["lesson"] for item in exit_bank
        }
        assert len(baseline) == len({item["lesson"] for item in baseline})
        for lesson in {item["lesson"] for item in exit_bank}:
            assert sum(item["lesson"] == lesson for item in exit_bank) == 2


def test_baseline_reports_competencies_and_specific_gaps():
    bank = BASELINE_BANKS[1]
    answers = _correct(bank)
    answers[0] = (answers[0] + 1) % len(bank[0]["options"])
    result = find_your_level.grade_baseline(1, answers)
    assert result["strong_evidence"] is False
    assert result["competency_scores"]["tokens_budget"] == 0
    assert result["gaps"][0]["lesson"] == "1.1"
    assert result["gaps"][0]["diagnosis"]


def test_exit_quiz_all_correct():
    for phase, bank in BANKS.items():
        result = check_understanding.run_quiz(phase, _correct(bank))
        assert result["verdict"] == "освоено"
        assert result["review_lessons"] == []
        assert result["retry_tasks"] == []


def test_exit_quiz_returns_diagnostic_feedback_and_open_retry():
    bank = BANKS[1]
    result = check_understanding.run_quiz(1, _wrong(bank))
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
    result = check_understanding.run_quiz(4, answers)
    assert result["score"] == 0.8
    assert result["coverage_ok"] is False
    assert result["verdict"] == "нужна практика"


def test_fixed_answer_position_cannot_pass_any_exit_bank():
    for phase, bank in BANKS.items():
        for choice in range(4):
            result = check_understanding.run_quiz(phase, [choice] * len(bank))
            assert result["verdict"] == "нужна практика"
            assert result["score"] < 0.8


def test_progress_is_directional_not_presented_as_exact_growth():
    bank = BANKS[8]
    baseline = {item["competency"]: 0.0 for item in bank}
    result = check_understanding.run_quiz(8, _correct(bank), baseline=baseline)
    assert {item["delta"] for item in result["progress"]} == {1.0}
    assert "не точное измерение" in result["progress_note"]


def test_check_understanding_cli_works_outside_skill_directory(tmp_path):
    script = ROOT / ".claude/skills/check-understanding/check_understanding.py"
    answers = ",".join(map(str, _correct(BANKS[1])))
    completed = subprocess.run(
        [sys.executable, str(script), "--phase", "1", "--answers", answers],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)
    assert result["verdict"] == "освоено"


def test_find_your_level_cli_works_outside_skill_directory(tmp_path):
    script = ROOT / ".claude/skills/find-your-level/find_your_level.py"
    output = tmp_path / "personal-route.md"
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--interactive",
            "--output",
            str(output),
            "--work-task",
            "Проверить изменение в репозитории",
            "--success-criterion",
            "Все тесты проходят",
            "--agent-role",
            "рабочий кандидат",
        ],
        cwd=tmp_path,
        input="0\n" * len(SELF_ASSESSMENT),
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Маршрут сохранён" in completed.stdout
    markdown = output.read_text(encoding="utf-8")
    assert "# Персональный маршрут AI Native" in markdown
    assert "**Сквозная задача из 0.1:** Проверить изменение в репозитории" in markdown
    assert "**Критерий успеха:** Все тесты проходят" in markdown
    assert "**Роль агента:** рабочий кандидат" in markdown


def test_compare_rejects_invalid_baseline_score():
    result = check_understanding.run_quiz(1, _correct(BANKS[1]))
    with pytest.raises(ValueError):
        check_understanding.compare_with_baseline(result, {"tokens_budget": 1.5})


def test_invalid_answer_index_is_rejected():
    with pytest.raises(ValueError):
        find_your_level.self_profile([0] * (len(SELF_ASSESSMENT) - 1) + [4])
    with pytest.raises(ValueError):
        check_understanding.run_quiz(1, [0] * (len(BANKS[1]) - 1))
