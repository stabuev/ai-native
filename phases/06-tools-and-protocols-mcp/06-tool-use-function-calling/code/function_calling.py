"""Tool use / function calling изнутри — Build It для урока 6.1.

Без зависимостей. Показывает протокол tool use: у инструмента есть JSON-схема,
модель возвращает tool_call (имя + аргументы), диспетчер валидирует аргументы по
схеме и исполняет, результат (tool_result) возвращается модели — и так до финала.
Модель здесь детерминированная (stub), чтобы урок шёл офлайн.
"""
from dataclasses import dataclass
from typing import Callable

_TYPES = {"string": str, "number": (int, float), "integer": int,
          "boolean": bool, "array": list, "object": dict}


@dataclass
class Tool:
    name: str
    description: str
    schema: dict          # {"properties": {...}, "required": [...]}
    fn: Callable


def validate_args(args, schema):
    """Проверить аргументы по мини JSON-схеме. Список ошибок (пустой = ок)."""
    errors = []
    for req in schema.get("required", []):
        if req not in args:
            errors.append(f"нет обязательного аргумента: {req}")
    props = schema.get("properties", {})
    for key, val in args.items():
        t = props.get(key, {}).get("type")
        if t and not isinstance(val, _TYPES.get(t, object)):
            errors.append(f"{key}: ожидался {t}")
    return errors


class ToolError(Exception):
    pass


def dispatch(tool_call, registry):
    """tool_call = {name, arguments}. Валидирует по схеме и исполняет инструмент."""
    name = tool_call["name"]
    args = tool_call.get("arguments", {})
    if name not in registry:
        raise ToolError(f"неизвестный инструмент: {name}")
    errs = validate_args(args, registry[name].schema)
    if errs:
        raise ToolError(f"невалидные аргументы: {errs}")
    return registry[name].fn(**args)


def run(model_fn, registry, max_steps=5):
    """Цикл tool use: model_fn -> tool_call | final; tool_result возвращается в историю."""
    history = []
    for _ in range(max_steps):
        step = model_fn(history)
        if step.get("type") == "final":
            return step["answer"], history
        result = dispatch(step["tool_call"], registry)
        history.append({"call": step["tool_call"], "result": result})
    raise ToolError("нет финала за max_steps")


# --- демо: инструмент + детерминированная «модель» ---
def _add(a, b):
    return a + b


REGISTRY = {
    "add": Tool("add", "сложить два числа",
                {"properties": {"a": {"type": "number"}, "b": {"type": "number"}},
                 "required": ["a", "b"]}, _add),
}


def _demo_model(history):
    if not history:
        return {"type": "tool_call", "tool_call": {"name": "add", "arguments": {"a": 2, "b": 3}}}
    return {"type": "final", "answer": history[-1]["result"]}


if __name__ == "__main__":
    answer, history = run(_demo_model, REGISTRY)
    print("История:", history)
    print("Ответ:", answer)
