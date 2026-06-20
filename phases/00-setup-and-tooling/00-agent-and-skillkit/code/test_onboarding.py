from find_your_level import QUESTIONS, PHASES, score, level, route
from check_understanding import run_quiz, BANKS


def test_score_range_and_levels():
    assert score([0] * len(QUESTIONS)) == 0
    assert score([3] * len(QUESTIONS)) == 30
    assert level(9) == "Новичок"
    assert level(10) == "Практик"
    assert level(20) == "Практик"
    assert level(21) == "Инженер"


def test_route_beginner_is_full_200h():
    r = route(score([0] * len(QUESTIONS)))
    assert r["level"] == "Новичок"
    assert r["total_hours"] == 200
    assert all(p["action"] == "focus" for p in r["plan"])


def test_route_engineer_is_shorter_but_keeps_capstone():
    r = route(score([3] * len(QUESTIONS)))
    assert r["level"] == "Инженер"
    assert r["total_hours"] < 200
    plan = {p["phase"]: p["action"] for p in r["plan"]}
    assert plan[0] == "skip"        # инженер пропускает setup
    assert plan[12] == "focus"      # capstone делают все
    assert len(r["plan"]) == len(PHASES) == 13


def test_check_understanding_all_correct():
    bank = BANKS[1]
    res = run_quiz(1, [q["correct"] for q in bank])
    assert res["verdict"] == "сдано"
    assert res["review_lessons"] == []


def test_check_understanding_flags_review_lessons():
    bank = BANKS[1]
    answers = [(q["correct"] + 1) % len(q["options"]) for q in bank]  # все мимо
    res = run_quiz(1, answers)
    assert res["verdict"] == "повторить"
    assert "1.1" in res["review_lessons"]
