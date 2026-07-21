from agent_eval import evaluate_agent, compare_versions, has_regression

CASES = [{"input": "2+2", "expected": "4"}, {"input": "3*3", "expected": "9"},
         {"input": "10-7", "expected": "3"}]
GOOD = lambda x: str(eval(x))
BROKEN = lambda x: "?"
HALF = lambda x: "4"            # угадывает только первый кейс


def test_perfect_agent_scores_one():
    assert evaluate_agent(GOOD, CASES)["success_rate"] == 1.0


def test_broken_agent_scores_zero():
    res = evaluate_agent(BROKEN, CASES)
    assert res["success_rate"] == 0.0
    assert len(res["per_case"]) == 3


def test_compare_versions_ranks_best_first():
    ranking = compare_versions({"good": GOOD, "broken": BROKEN, "half": HALF}, CASES)
    assert ranking[0][0] == "good"
    assert ranking[-1][0] == "broken"


def test_regression_detection():
    assert has_regression(GOOD, BROKEN, CASES) is True
    assert has_regression(GOOD, GOOD, CASES) is False
