from cost_router import cascade, always_top_cost, CASCADE


def answer_fn(model, req):
    return f"[{model}] ответ"


def quality_fn(req, ans):
    if "сложн" in req.lower():
        return 0.9 if "opus" in ans else 0.4     # сложное тянет только opus
    return 0.9                                    # простое — любая модель


def test_easy_stops_at_cheapest():
    res = cascade("простой вопрос", answer_fn, quality_fn)
    assert res["model"] == "gemini-flash"
    assert res["cost"] == 1


def test_hard_escalates_to_top():
    res = cascade("сложный вопрос", answer_fn, quality_fn)
    assert res["model"] == "opus-4.8"
    assert res["quality"] >= 0.7


def test_cascade_cheaper_than_always_top_on_mixed_workload():
    workload = ["простой", "простой", "простой", "сложный"]
    total = sum(cascade(r, answer_fn, quality_fn)["cost"] for r in workload)
    always_top = always_top_cost() * len(workload)
    assert total < always_top          # каскад экономит на простых запросах


def test_returns_best_when_none_pass_gate():
    res = cascade("сложный", answer_fn, lambda r, a: 0.1)   # никто не проходит gate
    assert res["model"] == CASCADE[-1][0]
