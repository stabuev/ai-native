from eval_harness import exact_match, contains, evaluate, compare

CASES = [
    {"input": "2+2", "expected": "4"},
    {"input": "3+5", "expected": "8"},
    {"input": "10-4", "expected": "6"},
]


def test_metrics():
    assert exact_match("4", "4") == 1.0
    assert exact_match("4 ", "4") == 1.0          # игнор пробелов
    assert exact_match("5", "4") == 0.0
    assert contains("ответ: 4", "4") == 1.0
    assert contains("нет", "4") == 0.0


def test_evaluate_scores_perfect_and_zero():
    good = evaluate(lambda x: str(eval(x)), CASES)
    assert good["score"] == 1.0
    assert len(good["per_case"]) == 3
    bad = evaluate(lambda x: "?", CASES)
    assert bad["score"] == 0.0


def test_compare_ranks_better_prompt_first():
    versions = {
        "good": lambda x: str(eval(x)),
        "half": lambda x: "4",                    # угадывает только первый кейс
        "bad": lambda x: "?",
    }
    ranking = compare(versions, CASES)
    assert ranking[0][0] == "good"
    assert ranking[-1][0] == "bad"
    assert ranking[0][1] > ranking[1][1] > ranking[2][1]
