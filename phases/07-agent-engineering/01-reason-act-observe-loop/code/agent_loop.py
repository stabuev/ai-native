"""Минимальный agent runtime для урока 7.1.

Decision policy выбирает следующее наблюдаемое действие из цели и execution
trace. Runtime проверяет действие, вызывает разрешённый инструмент и возвращает
policy структурированный результат. Внешняя модель для этого механизма не нужна:
в уроке её заменяет детерминированный test double с настоящим ветвлением.
"""

from dataclasses import dataclass, field
from inspect import signature
from typing import Callable


Tool = Callable[..., object]
DecisionPolicy = Callable[[dict, list["Step"]], "Action"]


@dataclass(frozen=True)
class Action:
    """Наблюдаемое решение policy: вызвать tool или завершить задачу."""

    kind: str  # "tool" | "final"
    action_id: str | None = None
    tool: str | None = None
    arguments: dict[str, object] = field(default_factory=dict)
    answer: object = None


@dataclass(frozen=True)
class Observation:
    """Структурированный результат одной попытки выполнить Action."""

    action_id: str
    ok: bool
    output: object = None
    error_code: str | None = None


@dataclass(frozen=True)
class Step:
    action: Action
    observation: Observation


class AgentError(Exception):
    """Ошибка самого runtime: нарушен контракт или исчерпан бюджет."""


def _failure(action_id: str, error_code: str) -> Observation:
    return Observation(action_id=action_id, ok=False, error_code=error_code)


def _execute(action: Action, tools: dict[str, Tool]) -> Observation:
    """Проверить Action и безопасно превратить результат в Observation."""

    action_id = action.action_id or ""
    if not action.tool or action.tool not in tools:
        return _failure(action_id, "unknown_tool")
    if not isinstance(action.arguments, dict):
        return _failure(action_id, "invalid_arguments")

    tool = tools[action.tool]
    try:
        signature(tool).bind(**action.arguments)
    except (TypeError, ValueError):
        return _failure(action_id, "invalid_arguments")

    try:
        output = tool(**action.arguments)
    except Exception:
        # В trace попадает стабильный безопасный код, а не сырой exception,
        # который может содержать внутренние данные инструмента.
        return _failure(action_id, "tool_error")
    return Observation(action_id=action_id, ok=True, output=output)


def run_agent(
    goal: dict,
    tools: dict[str, Tool],
    decision_policy: DecisionPolicy,
    max_steps: int = 6,
    trace: bool = False,
) -> tuple[object, list[Step]]:
    """Выполнить reason -> act -> observe до final или исчерпания бюджета.

    ``max_steps`` ограничивает попытки действий, а не финальное решение. После
    последнего разрешённого observation policy ещё может вернуть final, но новый
    tool action будет остановлен до side effect.
    """

    if max_steps < 0:
        raise AgentError("max_steps must be non-negative")

    execution_trace: list[Step] = []
    seen_action_ids: set[str] = set()

    while True:
        action = decision_policy(goal, execution_trace)  # reason: выбрать действие
        if not isinstance(action, Action):
            raise AgentError("decision policy must return Action")

        if action.kind == "final":
            if action.tool is not None or action.arguments:
                raise AgentError("final action cannot contain tool arguments")
            if trace:
                print(f"FINAL -> {action.answer}")
            return action.answer, execution_trace

        if action.kind != "tool":
            raise AgentError(f"unknown action kind: {action.kind}")
        if len(execution_trace) >= max_steps:
            raise AgentError(f"step budget exhausted: {max_steps}")
        if not action.action_id:
            raise AgentError("tool action requires action_id")
        if action.action_id in seen_action_ids:
            raise AgentError(f"duplicate action_id: {action.action_id}")

        seen_action_ids.add(action.action_id)
        observation = _execute(action, tools)  # act; ошибка тоже становится результатом
        execution_trace.append(Step(action, observation))  # observe

        if trace:
            result = observation.output if observation.ok else observation.error_code
            print(f"{action.action_id}: {action.tool} -> {result}")


# Офлайн-среда: две read-only capability для воспроизводимого упражнения.
_RELEASE_DECISIONS = {
    "run-ready": {"decision": "publish", "failed_checks": []},
    "run-review": {"decision": "review", "failed_checks": ["security"]},
}

_CHECK_REPORTS = {
    ("run-review", "security"): {
        "status": "failed",
        "summary": "dependency scan requires a human review",
    }
}


def get_release_decision(*, run_id: str) -> dict:
    """Вернуть сохранённое решение по прогону или сигнализировать об ошибке."""

    if run_id not in _RELEASE_DECISIONS:
        raise LookupError("run is unavailable")
    return dict(_RELEASE_DECISIONS[run_id])


def get_check_report(*, run_id: str, check: str) -> dict:
    """Вернуть безопасную сводку по одной неуспешной проверке."""

    key = (run_id, check)
    if key not in _CHECK_REPORTS:
        raise LookupError("check report is unavailable")
    return dict(_CHECK_REPORTS[key])


TOOLS: dict[str, Tool] = {
    "get_release_decision": get_release_decision,
    "get_check_report": get_check_report,
}


class ReleaseDecisionPolicy:
    """Детерминированный test double для decision policy.

    Маршрут не передаётся в goal. Policy выбирает его после каждого observation:
    успешный publish завершает задачу, review открывает диагностическую ветку,
    а временная ошибка первого чтения допускает одну повторную попытку.
    """

    def __call__(self, goal: dict, execution_trace: list[Step]) -> Action:
        run_id = goal["run_id"]

        if not execution_trace:
            return Action(
                kind="tool",
                action_id="decision-1",
                tool="get_release_decision",
                arguments={"run_id": run_id},
            )

        last = execution_trace[-1]
        observation = last.observation

        if last.action.tool == "get_release_decision":
            attempts = sum(
                step.action.tool == "get_release_decision"
                for step in execution_trace
            )
            if not observation.ok:
                if attempts < 2:
                    return Action(
                        kind="tool",
                        action_id=f"decision-{attempts + 1}",
                        tool="get_release_decision",
                        arguments={"run_id": run_id},
                    )
                return Action(
                    kind="final",
                    answer={
                        "run_id": run_id,
                        "decision": "unknown",
                        "summary": "release decision is unavailable",
                    },
                )

            result = observation.output
            decision = result["decision"]
            failed_checks = result.get("failed_checks", [])

            if decision == "publish":
                return Action(
                    kind="final",
                    answer={
                        "run_id": run_id,
                        "decision": "publish",
                        "summary": "all required checks passed",
                    },
                )
            if failed_checks:
                check = failed_checks[0]
                return Action(
                    kind="tool",
                    action_id=f"report-{check}",
                    tool="get_check_report",
                    arguments={"run_id": run_id, "check": check},
                )
            return Action(
                kind="final",
                answer={
                    "run_id": run_id,
                    "decision": decision,
                    "summary": "no diagnostic check was provided",
                },
            )

        if last.action.tool == "get_check_report":
            if observation.ok:
                return Action(
                    kind="final",
                    answer={
                        "run_id": run_id,
                        "decision": "review",
                        "summary": observation.output["summary"],
                    },
                )
            return Action(
                kind="final",
                answer={
                    "run_id": run_id,
                    "decision": "review",
                    "summary": "diagnostic report is unavailable",
                },
            )

        raise AgentError("release policy received an unexpected trace")


def make_release_decision_adapter(
    call_capability: Callable[..., object],
    trusted_context: dict[str, object],
) -> Tool:
    """Обернуть защищённую MCP capability в обычный инструмент runtime.

    Модель управляет только ``run_id``. Identity/scopes привязывает приложение
    вне public arguments; server-side access policy остаётся последней границей.
    """

    bound_context = dict(trusted_context)

    def adapter(*, run_id: str) -> object:
        return call_capability(
            capability="get_release_decision",
            arguments={"run_id": run_id},
            trusted_context=dict(bound_context),
        )

    return adapter


if __name__ == "__main__":
    for demo_run_id in ("run-ready", "run-review"):
        answer, steps = run_agent(
            {"run_id": demo_run_id},
            TOOLS,
            ReleaseDecisionPolicy(),
            trace=True,
        )
        print(f"{demo_run_id}: {answer} ({len(steps)} tool step(s))\n")
