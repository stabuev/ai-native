"""Явный план, рабочее состояние и checkpoint для урока 7.2.

Модуль не заменяет безопасный runtime из 7.1. Он добавляет слой управления
задачей вокруг контракта Action -> Observation: строит начальный план из цели,
обновляет именованные факты, пересматривает будущие шаги и сохраняет состояние
так, чтобы завершённый шаг не повторялся после перезапуска.
"""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class Action:
    """Тот же наблюдаемый контракт решения, что и в 7.1."""

    kind: str  # "tool" | "final"
    action_id: str | None = None
    tool: str | None = None
    arguments: dict[str, object] = field(default_factory=dict)
    answer: object = None


@dataclass(frozen=True)
class Observation:
    """Связанный с Action результат безопасного runtime из 7.1."""

    action_id: str
    ok: bool
    output: object = None
    error_code: str | None = None


@dataclass(frozen=True)
class TraceStep:
    action: Action
    observation: Observation


@dataclass
class PlanStep:
    """Один проверяемый пункт текущей версии плана."""

    step_id: str
    objective: str
    tool: str
    arguments: dict[str, object]
    success_criterion: str
    depends_on: list[str] = field(default_factory=list)
    status: str = "pending"  # pending | in_progress | completed | blocked | skipped


@dataclass
class TaskState:
    """Checkpointable state одной задачи, а не долговременная память пользователя."""

    goal: dict[str, object]
    plan_version: int
    plan: list[PlanStep]
    working_facts: dict[str, object] = field(default_factory=dict)
    execution_trace: list[TraceStep] = field(default_factory=list)
    status: str = "running"  # running | completed | blocked
    final_answer: object = None


class TaskStateError(Exception):
    """План или checkpoint нельзя безопасно продолжить автоматически."""


def create_initial_state(goal: dict[str, object]) -> TaskState:
    """Создать первый короткий план из высокоуровневой цели.

    Детерминированный planner — test double для офлайн-урока. В goal нет готового
    списка tool calls: дальнейшая ветка появится только после Observation.
    """

    if goal.get("objective") != "prepare_release_readiness":
        raise TaskStateError("unsupported objective")
    run_id = goal.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise TaskStateError("goal requires non-empty run_id")

    return TaskState(
        goal=dict(goal),
        plan_version=1,
        plan=[
            PlanStep(
                step_id="read-decision",
                objective="Получить защищённое решение по прогону",
                tool="get_release_decision",
                arguments={"run_id": run_id},
                success_criterion="Получен decision и список failed_checks",
            )
        ],
    )


def _completed_ids(state: TaskState) -> set[str]:
    return {step.step_id for step in state.plan if step.status == "completed"}


def decide_next(state: TaskState) -> Action:
    """Вернуть следующий Action и пометить выбранный шаг как in_progress."""

    if state.status == "completed":
        return Action(kind="final", answer=state.final_answer)
    if state.status == "blocked":
        raise TaskStateError("task is blocked; inspect state before continuing")

    in_progress = [step.step_id for step in state.plan if step.status == "in_progress"]
    if in_progress:
        raise TaskStateError(
            f"in-progress step requires reconciliation before resume: {in_progress[0]}"
        )

    completed = _completed_ids(state)
    for step in state.plan:
        if step.status == "pending" and set(step.depends_on) <= completed:
            step.status = "in_progress"
            return Action(
                kind="tool",
                action_id=step.step_id,
                tool=step.tool,
                arguments=dict(step.arguments),
            )

    state.status = "blocked"
    raise TaskStateError("no executable step: plan has unmet dependencies")


def _in_progress_step(state: TaskState, action_id: str) -> PlanStep:
    matches = [
        step
        for step in state.plan
        if step.step_id == action_id and step.status == "in_progress"
    ]
    if len(matches) != 1:
        raise TaskStateError(f"observation does not match in-progress step: {action_id}")
    return matches[0]


def _action_from_step(step: PlanStep) -> Action:
    return Action(
        kind="tool",
        action_id=step.step_id,
        tool=step.tool,
        arguments=dict(step.arguments),
    )


def _block(
    state: TaskState,
    step: PlanStep,
    observation: Observation,
    reason: str,
) -> None:
    step.status = "blocked"
    state.status = "blocked"
    state.working_facts["task.last_error"] = reason
    state.execution_trace.append(
        TraceStep(action=_action_from_step(step), observation=observation)
    )


def _valid_decision_output(output: object) -> bool:
    if not isinstance(output, dict):
        return False
    if output.get("decision") not in {"publish", "review", "block"}:
        return False
    failed_checks = output.get("failed_checks")
    return isinstance(failed_checks, list) and all(
        isinstance(check, str) and check for check in failed_checks
    )


def _valid_report_output(output: object) -> bool:
    return (
        isinstance(output, dict)
        and output.get("status") in {"passed", "failed"}
        and isinstance(output.get("summary"), str)
        and bool(output["summary"])
    )


def apply_observation(state: TaskState, observation: Observation) -> None:
    """Обновить trace, working state и будущий план после одного Observation."""

    step = _in_progress_step(state, observation.action_id)

    if not observation.ok:
        _block(state, step, observation, observation.error_code or "tool_error")
        return

    if step.tool == "get_release_decision":
        if not _valid_decision_output(observation.output):
            _block(state, step, observation, "invalid_decision_result")
            return

        result = observation.output
        step.status = "completed"
        state.execution_trace.append(
            TraceStep(action=_action_from_step(step), observation=observation)
        )
        state.working_facts["release.decision"] = result["decision"]
        state.working_facts["release.failed_checks"] = list(result["failed_checks"])

        if result["decision"] == "publish":
            state.status = "completed"
            state.final_answer = {
                "run_id": state.goal["run_id"],
                "decision": "publish",
                "summary": "all required checks passed",
            }
            return

        if not result["failed_checks"]:
            state.status = "blocked"
            state.working_facts["task.last_error"] = "missing_failed_check"
            return

        check = result["failed_checks"][0]
        state.plan.append(
            PlanStep(
                step_id=f"diagnose-{check}",
                objective=f"Получить безопасную сводку проверки {check}",
                tool="get_check_report",
                arguments={"run_id": state.goal["run_id"], "check": check},
                success_criterion="Получены status и непустой summary",
                depends_on=["read-decision"],
            )
        )
        state.plan_version += 1
        return

    if step.tool == "get_check_report":
        if not _valid_report_output(observation.output):
            _block(state, step, observation, "invalid_report_result")
            return

        result = observation.output
        step.status = "completed"
        state.execution_trace.append(
            TraceStep(action=_action_from_step(step), observation=observation)
        )
        state.working_facts["release.diagnostic_status"] = result["status"]
        state.working_facts["release.diagnostic_summary"] = result["summary"]
        state.status = "completed"
        state.final_answer = {
            "run_id": state.goal["run_id"],
            "decision": state.working_facts["release.decision"],
            "summary": result["summary"],
        }
        return

    _block(state, step, observation, "unsupported_plan_step")


class JsonCheckpointStore:
    """Файловый checkpoint с атомарной заменой готового JSON."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def save(self, state: TaskState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(asdict(state), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def load(self) -> TaskState:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return TaskState(
            goal=raw["goal"],
            plan_version=raw["plan_version"],
            plan=[PlanStep(**step) for step in raw["plan"]],
            working_facts=raw["working_facts"],
            execution_trace=[
                TraceStep(
                    action=Action(**item["action"]),
                    observation=Observation(**item["observation"]),
                )
                for item in raw["execution_trace"]
            ],
            status=raw["status"],
            final_answer=raw["final_answer"],
        )


Executor = Callable[[Action], Observation]


def advance_task(
    state: TaskState,
    execute_action: Executor,
    checkpoint: JsonCheckpointStore | None = None,
) -> Action:
    """Выполнить один переход, сохранив checkpoint до и после tool call."""

    action = decide_next(state)
    if action.kind == "final":
        if checkpoint:
            checkpoint.save(state)
        return action

    # Если процесс упадёт после side effect, останется in_progress. Такой шаг нельзя
    # бездумно повторять: следующий resume потребует reconciliation.
    if checkpoint:
        checkpoint.save(state)

    observation = execute_action(action)
    if not isinstance(observation, Observation):
        raise TaskStateError("executor must return Observation")
    apply_observation(state, observation)

    if checkpoint:
        checkpoint.save(state)
    return action


def run_to_completion(
    state: TaskState,
    execute_action: Executor,
    checkpoint: JsonCheckpointStore | None = None,
) -> object:
    """Повторять переходы до final; budget и tool guardrails остаются в executor 7.1."""

    while True:
        action = advance_task(state, execute_action, checkpoint)
        if action.kind == "final":
            return action.answer


def reference_executor(action: Action) -> Observation:
    """Офлайн test double среды; в переносе его заменяет runtime/MCP adapter 7.1."""

    decisions = {
        "run-ready": {"decision": "publish", "failed_checks": []},
        "run-review": {"decision": "review", "failed_checks": ["security"]},
    }
    reports = {
        ("run-review", "security"): {
            "status": "failed",
            "summary": "dependency scan requires a human review",
        }
    }

    if action.tool == "get_release_decision":
        output = decisions.get(action.arguments["run_id"])
    elif action.tool == "get_check_report":
        output = reports.get(
            (action.arguments["run_id"], action.arguments["check"])
        )
    else:
        output = None

    if output is None:
        return Observation(
            action_id=action.action_id or "",
            ok=False,
            error_code="not_found",
        )
    return Observation(
        action_id=action.action_id or "",
        ok=True,
        output=output,
    )


if __name__ == "__main__":
    for run_id in ("run-ready", "run-review"):
        task = create_initial_state(
            {"objective": "prepare_release_readiness", "run_id": run_id}
        )
        answer = run_to_completion(task, reference_executor)
        print(f"{run_id}: {answer}")
        print(
            "plan:",
            [(step.step_id, step.status) for step in task.plan],
            "version:",
            task.plan_version,
        )
        print("working facts:", task.working_facts)
        print("trace steps:", len(task.execution_trace), "\n")
