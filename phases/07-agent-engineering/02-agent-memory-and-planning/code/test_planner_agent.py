import pytest

from planner_agent import (
    JsonCheckpointStore,
    Observation,
    TaskStateError,
    advance_task,
    apply_observation,
    create_initial_state,
    decide_next,
    reference_executor,
    run_to_completion,
)


def goal(run_id="run-review"):
    return {"objective": "prepare_release_readiness", "run_id": run_id}


def test_initial_plan_comes_from_high_level_goal_without_prescribed_operations():
    state = create_initial_state(goal())

    assert "ops" not in state.goal
    assert state.plan_version == 1
    assert [step.step_id for step in state.plan] == ["read-decision"]
    assert state.working_facts == {}


def test_observation_changes_the_plan_and_named_working_state():
    state = create_initial_state(goal())
    action = decide_next(state)
    observation = Observation(
        action_id=action.action_id,
        ok=True,
        output={"decision": "review", "failed_checks": ["security"]},
    )

    apply_observation(state, observation)

    assert state.plan_version == 2
    assert [(step.step_id, step.status) for step in state.plan] == [
        ("read-decision", "completed"),
        ("diagnose-security", "pending"),
    ]
    assert state.working_facts == {
        "release.decision": "review",
        "release.failed_checks": ["security"],
    }
    assert state.execution_trace[0].observation.action_id == action.action_id


def test_publish_and_review_take_different_plan_routes():
    ready = create_initial_state(goal("run-ready"))
    review = create_initial_state(goal("run-review"))

    ready_answer = run_to_completion(ready, reference_executor)
    review_answer = run_to_completion(review, reference_executor)

    assert ready_answer["decision"] == "publish"
    assert len(ready.plan) == 1
    assert len(ready.execution_trace) == 1
    assert review_answer["decision"] == "review"
    assert len(review.plan) == 2
    assert len(review.execution_trace) == 2
    assert review.working_facts["release.diagnostic_status"] == "failed"


def test_invalid_observation_blocks_instead_of_fabricating_final_answer():
    state = create_initial_state(goal())
    action = decide_next(state)

    apply_observation(
        state,
        Observation(action_id=action.action_id, ok=True, output={"message": "looks ok"}),
    )

    assert state.status == "blocked"
    assert state.final_answer is None
    assert state.plan[0].status == "blocked"
    assert state.working_facts["task.last_error"] == "invalid_decision_result"


def test_unmet_dependency_cannot_execute():
    state = create_initial_state(goal())
    state.plan[0].status = "skipped"
    state.plan.append(
        type(state.plan[0])(
            step_id="diagnose-security",
            objective="diagnose",
            tool="get_check_report",
            arguments={"run_id": "run-review", "check": "security"},
            success_criterion="report exists",
            depends_on=["read-decision"],
        )
    )

    with pytest.raises(TaskStateError, match="unmet dependencies"):
        decide_next(state)

    assert state.status == "blocked"


def test_checkpoint_resume_does_not_repeat_completed_step(tmp_path):
    calls = []

    def recording_executor(action):
        calls.append(action.tool)
        return reference_executor(action)

    store = JsonCheckpointStore(tmp_path / "task.json")
    state = create_initial_state(goal())
    advance_task(state, recording_executor, store)

    resumed = store.load()
    assert resumed.plan_version == 2
    assert [(step.step_id, step.status) for step in resumed.plan] == [
        ("read-decision", "completed"),
        ("diagnose-security", "pending"),
    ]
    assert resumed.working_facts["release.failed_checks"] == ["security"]
    assert len(resumed.execution_trace) == 1

    answer = run_to_completion(resumed, recording_executor, store)

    assert answer["decision"] == "review"
    assert calls == ["get_release_decision", "get_check_report"]
    assert [step.status for step in resumed.plan] == ["completed", "completed"]


def test_in_progress_checkpoint_requires_reconciliation_before_resume(tmp_path):
    store = JsonCheckpointStore(tmp_path / "ambiguous.json")
    state = create_initial_state(goal())
    decide_next(state)  # checkpoint между выбором Action и получением Observation
    store.save(state)

    resumed = store.load()
    with pytest.raises(TaskStateError, match="requires reconciliation"):
        decide_next(resumed)


def test_tool_error_is_evidence_and_blocks_automatic_continuation():
    state = create_initial_state(goal())
    action = decide_next(state)
    apply_observation(
        state,
        Observation(action_id=action.action_id, ok=False, error_code="tool_error"),
    )

    assert state.status == "blocked"
    assert state.working_facts["task.last_error"] == "tool_error"
    assert state.execution_trace[-1].observation.error_code == "tool_error"
