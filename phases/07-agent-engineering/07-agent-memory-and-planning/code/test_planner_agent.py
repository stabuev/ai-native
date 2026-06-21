from planner_agent import Memory, plan, run

GOAL = {"start": 2, "ops": [("add", 3), ("mul", 4), ("sub", 1)]}   # (2+3)*4-1 = 19


def test_plan_decomposes_into_steps():
    steps = plan(GOAL)
    assert len(steps) == 3
    assert steps[0] == {"op": "add", "operand": 3}


def test_run_computes_through_memory():
    answer, memory, trace = run(GOAL)
    assert answer == 19
    assert len(trace) == 3
    assert memory.recall("value") == 19


def test_memory_holds_intermediate_steps():
    _, memory, _ = run(GOAL)
    assert memory.recall("step_0") == 5      # 2+3
    assert memory.recall("step_1") == 20     # *4


def test_memory_remember_recall():
    m = Memory()
    m.remember("k", 42)
    assert m.recall("k") == 42
    assert m.recall("missing", "def") == "def"
