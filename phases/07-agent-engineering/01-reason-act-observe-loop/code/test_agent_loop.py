import pytest

from agent_loop import (
    Action,
    AgentError,
    ReleaseDecisionPolicy,
    TOOLS,
    make_release_decision_adapter,
    run_agent,
)


def test_observation_changes_the_route():
    ready_answer, ready_trace = run_agent(
        {"run_id": "run-ready"}, TOOLS, ReleaseDecisionPolicy()
    )
    review_answer, review_trace = run_agent(
        {"run_id": "run-review"}, TOOLS, ReleaseDecisionPolicy()
    )

    assert ready_answer["decision"] == "publish"
    assert [step.action.tool for step in ready_trace] == ["get_release_decision"]
    assert review_answer["decision"] == "review"
    assert [step.action.tool for step in review_trace] == [
        "get_release_decision",
        "get_check_report",
    ]


def test_action_and_observation_are_correlated_and_keep_named_arguments():
    _, execution_trace = run_agent(
        {"run_id": "run-review"}, TOOLS, ReleaseDecisionPolicy()
    )

    for step in execution_trace:
        assert step.observation.action_id == step.action.action_id
        assert isinstance(step.action.arguments, dict)
    assert execution_trace[1].action.arguments == {
        "run_id": "run-review",
        "check": "security",
    }


@pytest.mark.parametrize(
    ("tool_name", "arguments", "error_code"),
    [
        ("delete_release", {"run_id": "run-ready"}, "unknown_tool"),
        ("get_release_decision", {"wrong_name": "run-ready"}, "invalid_arguments"),
    ],
)
def test_rejected_action_does_not_execute_tool(tool_name, arguments, error_code):
    calls = []

    def protected_tool(*, run_id):
        calls.append(run_id)
        return {"decision": "publish", "failed_checks": []}

    def correcting_policy(goal, execution_trace):
        if not execution_trace:
            return Action(
                kind="tool",
                action_id="bad-1",
                tool=tool_name,
                arguments=arguments,
            )
        assert execution_trace[-1].observation.error_code == error_code
        return Action(kind="final", answer="stopped safely")

    answer, execution_trace = run_agent(
        {}, {"get_release_decision": protected_tool}, correcting_policy
    )

    assert answer == "stopped safely"
    assert execution_trace[0].observation.ok is False
    assert calls == []


def test_tool_failure_becomes_observation_and_policy_recovers_once():
    calls = 0

    def flaky_decision(*, run_id):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TimeoutError("internal address must not enter the trace")
        return {"decision": "publish", "failed_checks": []}

    answer, execution_trace = run_agent(
        {"run_id": "run-ready"},
        {
            "get_release_decision": flaky_decision,
            "get_check_report": TOOLS["get_check_report"],
        },
        ReleaseDecisionPolicy(),
    )

    assert answer["decision"] == "publish"
    assert calls == 2
    assert execution_trace[0].observation.error_code == "tool_error"
    assert "internal address" not in repr(execution_trace)
    assert execution_trace[1].observation.ok is True


def test_budget_blocks_the_next_side_effect():
    calls = []

    def record_call(*, value):
        calls.append(value)
        return value

    def endless_policy(goal, execution_trace):
        step = len(execution_trace) + 1
        return Action(
            kind="tool",
            action_id=f"call-{step}",
            tool="record_call",
            arguments={"value": step},
        )

    with pytest.raises(AgentError, match="step budget exhausted"):
        run_agent({}, {"record_call": record_call}, endless_policy, max_steps=2)

    assert calls == [1, 2]


def test_duplicate_action_id_is_rejected_before_second_execution():
    calls = []

    def record_call(*, value):
        calls.append(value)
        return value

    policy = lambda goal, execution_trace: Action(
        kind="tool",
        action_id="same-id",
        tool="record_call",
        arguments={"value": len(execution_trace)},
    )

    with pytest.raises(AgentError, match="duplicate action_id"):
        run_agent({}, {"record_call": record_call}, policy)

    assert calls == [0]


def test_mcp_adapter_keeps_trusted_context_outside_model_arguments():
    captured = {}

    def fake_transport(**request):
        captured.update(request)
        return {"decision": "publish", "failed_checks": []}

    adapter = make_release_decision_adapter(
        fake_transport,
        trusted_context={"actor": "local-user", "scopes": ["release_decision:read"]},
    )
    answer, execution_trace = run_agent(
        {"run_id": "run-ready"},
        {"get_release_decision": adapter},
        ReleaseDecisionPolicy(),
    )

    assert answer["decision"] == "publish"
    assert execution_trace[0].action.arguments == {"run_id": "run-ready"}
    assert captured["arguments"] == {"run_id": "run-ready"}
    assert captured["trusted_context"] == {
        "actor": "local-user",
        "scopes": ["release_decision:read"],
    }
