"""Минимальный client-side tool-use runtime для урока 6.1.

Модель получает пользовательский запрос и только публичные описания инструментов.
Она может вернуть ``tool_call`` или ``final``. Runtime сопоставляет вызов с локальным
allowlist, проверяет аргументы, исполняет Python-функцию и возвращает связанный
``tool_result``. Детерминированный stub заменяет сеть и LLM, но не скрывает протокол.

Валидатор ниже поддерживает намеренно ограниченное подмножество JSON Schema:
``type: object``, ``properties``, ``required``, ``additionalProperties`` и ``enum``
для полей верхнего уровня. Это учебная граница, а не реализация стандарта целиком.
"""

from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass
import json
import math
from typing import Any


@dataclass(frozen=True)
class Tool:
    """Публичный контракт инструмента и скрытая локальная реализация."""

    name: str
    description: str
    schema: dict[str, Any]
    fn: Callable[..., Any]


class ToolError(Exception):
    """Вызов нельзя безопасно передать локальному инструменту."""


def public_tool_specs(registry: Mapping[str, Tool]) -> list[dict[str, Any]]:
    """Вернуть только name, description и input schema — без Python callable."""

    return [
        {
            "name": tool.name,
            "description": tool.description,
            "input_schema": deepcopy(tool.schema),
        }
        for tool in registry.values()
    ]


def _matches_json_type(value: Any, expected: str) -> bool:
    """Проверить базовый JSON-тип без Python-ловушки ``bool`` как ``int``."""

    if expected == "string":
        return isinstance(value, str)
    if expected == "number":
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        )
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "null":
        return value is None
    return False


def validate_args(args: Any, schema: Mapping[str, Any]) -> list[str]:
    """Проверить аргументы по объявленному учебному подмножеству JSON Schema."""

    if not isinstance(args, Mapping):
        return ["arguments: ожидался object"]
    if schema.get("type", "object") != "object":
        return ["schema: поддерживается только type=object"]

    errors: list[str] = []
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    for name in required:
        if name not in args:
            errors.append(f"нет обязательного аргумента: {name}")

    if schema.get("additionalProperties") is False:
        for name in args:
            if name not in properties:
                errors.append(f"неизвестный аргумент: {name}")

    for name, value in args.items():
        rule = properties.get(name)
        if not isinstance(rule, Mapping):
            continue
        expected = rule.get("type")
        if expected and not _matches_json_type(value, expected):
            errors.append(f"{name}: ожидался {expected}")
            continue
        if "enum" in rule and value not in rule["enum"]:
            allowed = ", ".join(map(str, rule["enum"]))
            errors.append(f"{name}: значение не входит в enum [{allowed}]")

    return errors


def dispatch(
    tool_call: Mapping[str, Any], registry: Mapping[str, Tool]
) -> dict[str, Any]:
    """Проверить allowlist и аргументы, затем вернуть связанный tool_result."""

    if not isinstance(tool_call, Mapping):
        raise ToolError("tool_call должен быть object")

    call_id = tool_call.get("id")
    name = tool_call.get("name")
    arguments = tool_call.get("arguments", {})
    if not isinstance(call_id, str) or not call_id.strip():
        raise ToolError("tool_call.id обязателен")
    if not isinstance(name, str) or not name.strip():
        raise ToolError("tool_call.name обязателен")
    if name not in registry:
        raise ToolError(f"неизвестный инструмент: {name}")

    errors = validate_args(arguments, registry[name].schema)
    if errors:
        raise ToolError("невалидные аргументы: " + "; ".join(errors))

    content = registry[name].fn(**dict(arguments))
    return {
        "type": "tool_result",
        "call_id": call_id,
        "ok": True,
        "content": content,
    }


def run(
    model_fn: Callable[[list[dict[str, Any]], list[dict[str, Any]]], Mapping[str, Any]],
    registry: Mapping[str, Tool],
    user_request: str,
    *,
    max_tool_calls: int = 3,
) -> tuple[Any, list[dict[str, Any]]]:
    """Вести model → tool_call → tool_result до final с ограничением вызовов."""

    if not isinstance(user_request, str) or not user_request.strip():
        raise ValueError("user_request должен быть непустой строкой")
    if (
        not isinstance(max_tool_calls, int)
        or isinstance(max_tool_calls, bool)
        or max_tool_calls < 1
    ):
        raise ValueError("max_tool_calls должен быть положительным целым")

    history: list[dict[str, Any]] = [
        {"type": "user", "content": user_request}
    ]
    tool_specs = public_tool_specs(registry)
    used_calls = 0

    while True:
        step = model_fn(deepcopy(history), deepcopy(tool_specs))
        if not isinstance(step, Mapping):
            raise ToolError("модель должна вернуть object")
        step = dict(step)

        if step.get("type") == "final":
            if "answer" not in step:
                raise ToolError("final должен содержать answer")
            history.append(deepcopy(step))
            return step["answer"], history

        if step.get("type") != "tool_call":
            raise ToolError("ожидался ответ type=tool_call или type=final")

        call_id = step.get("id")
        if not isinstance(call_id, str) or not call_id.strip():
            raise ToolError("tool_call.id обязателен для связи с result")
        if used_calls >= max_tool_calls:
            raise ToolError("превышен лимит max_tool_calls")

        used_calls += 1
        history.append(deepcopy(step))
        try:
            result = dispatch(step, registry)
        except ToolError as error:
            result = {
                "type": "tool_result",
                "call_id": call_id,
                "ok": False,
                "error": str(error),
            }
        history.append(result)


REPORTS = {
    "phase-5-paid-revenue-q2": {
        "decision": "publish",
        "metric_id": "paid_revenue",
        "as_of": "2026-07-01",
    },
    "phase-5-unfinished": {
        "decision": "block",
        "metric_id": "paid_revenue",
        "as_of": "2026-07-01",
    },
}


def _add(a: float, b: float) -> float:
    return a + b


def _get_release_decision(run_id: str) -> dict[str, str]:
    return deepcopy(REPORTS[run_id])


REGISTRY = {
    "add": Tool(
        name="add",
        description="Сложить два числа, когда пользователю нужен точный расчёт суммы.",
        schema={
            "type": "object",
            "properties": {
                "a": {"type": "number"},
                "b": {"type": "number"},
            },
            "required": ["a", "b"],
            "additionalProperties": False,
        },
        fn=_add,
    ),
    "get_release_decision": Tool(
        name="get_release_decision",
        description=(
            "Получить сохранённое решение quality gate по точному run_id; "
            "использовать для чтения результата, но не для изменения policy."
        ),
        schema={
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "string",
                    "enum": list(REPORTS),
                }
            },
            "required": ["run_id"],
            "additionalProperties": False,
        },
        fn=_get_release_decision,
    ),
}


DEMO_REQUEST = "Какое решение у запуска phase-5-paid-revenue-q2?"


def _demo_model(
    history: list[dict[str, Any]], tool_specs: list[dict[str, Any]]
) -> dict[str, Any]:
    """Детерминированный protocol stub: не оценивает качество реальной LLM."""

    available = {spec["name"] for spec in tool_specs}
    results = [event for event in history if event.get("type") == "tool_result"]

    if not results:
        if "get_release_decision" not in available:
            return {"type": "final", "answer": "Инструмент недоступен."}
        return {
            "type": "tool_call",
            "id": "call-release-1",
            "name": "get_release_decision",
            "arguments": {"run_id": "phase-5-paid-revenue-q2"},
        }

    result = results[-1]
    if not result["ok"]:
        return {"type": "final", "answer": f"Вызов отклонён: {result['error']}"}

    report = result["content"]
    return {
        "type": "final",
        "answer": (
            f"Решение: {report['decision']} "
            f"для {report['metric_id']} на {report['as_of']}."
        ),
    }


if __name__ == "__main__":
    answer, trace = run(_demo_model, REGISTRY, DEMO_REQUEST)
    print(json.dumps(trace, ensure_ascii=False, indent=2))
    print("Финальный ответ:", answer)
