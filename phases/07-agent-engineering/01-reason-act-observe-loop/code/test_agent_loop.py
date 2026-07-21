import pytest
from agent_loop import run_agent, RuleBasedPolicy, Action, AgentError, TOOLS


def test_chains_operations():
    goal = {"start": 2, "ops": [("add", 3), ("mul", 4)]}
    answer, history = run_agent(goal, TOOLS, RuleBasedPolicy())
    assert answer == 20            # (2 + 3) * 4
    assert len(history) == 2       # ровно два вызова инструментов


def test_observation_feeds_next_step():
    goal = {"start": 10, "ops": [("sub", 4), ("mul", 2)]}
    answer, history = run_agent(goal, TOOLS, RuleBasedPolicy())
    assert history[0].observation == 6     # 10 - 4
    assert answer == 12                    # 6 * 2


def test_no_ops_returns_start():
    answer, history = run_agent({"start": 7, "ops": []}, TOOLS, RuleBasedPolicy())
    assert answer == 7
    assert history == []


def test_max_steps_guardrail():
    # policy, которая никогда не финиширует -> должен сработать guardrail
    loop_policy = lambda goal, history: Action(kind="tool", tool="add", args=(1, 1))
    with pytest.raises(AgentError):
        run_agent({"start": 0, "ops": []}, TOOLS, loop_policy, max_steps=3)


def test_unknown_tool_raises():
    bad = lambda goal, history: Action(kind="tool", tool="divide", args=(1, 1))
    with pytest.raises(AgentError):
        run_agent({"start": 0, "ops": []}, TOOLS, bad)
