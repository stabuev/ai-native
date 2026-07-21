from agent_failures import detect_loop, goal_relatedness, run_guarded


def test_detect_loop():
    assert detect_loop(["x", "x", "x"]) is True
    assert detect_loop(["a", "b", "a"]) is False
    assert detect_loop(["x", "x"], repeat=3) is False     # мало шагов


def test_goal_relatedness():
    assert goal_relatedness("найти отчёт по продажам", "найти отчёт") == 1.0
    assert goal_relatedness("найти отчёт", "купить пиццу") == 0.0


def test_run_guarded_detects_loop():
    res = run_guarded(lambda actions: "refresh", max_steps=10)
    assert res["status"] == "loop_detected"


def test_run_guarded_completes():
    seq = ["search", "read", "answer"]
    res = run_guarded(lambda a: seq[len(a)] if len(a) < len(seq) else "DONE")
    assert res["status"] == "done"
    assert res["actions"] == seq


def test_run_guarded_hits_step_limit():
    res = run_guarded(lambda a: f"step_{len(a)}", max_steps=5)
    assert res["status"] == "step_limit"
    assert len(res["actions"]) == 5


def test_run_guarded_detects_drift():
    # действия не относятся к цели → дрейф
    res = run_guarded(lambda a: "смотрю мемы", goal="сделать отчёт",
                      max_steps=5, drift_threshold=0.5)
    assert res["status"] == "goal_drift"
