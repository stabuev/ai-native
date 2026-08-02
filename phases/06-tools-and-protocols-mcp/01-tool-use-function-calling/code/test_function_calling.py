import pytest

from function_calling import (
    DEMO_REQUEST,
    REGISTRY,
    Tool,
    ToolError,
    _demo_model,
    dispatch,
    public_tool_specs,
    run,
    validate_args,
)


STRICT_SCHEMA = {
    "type": "object",
    "properties": {
        "count": {"type": "integer"},
        "mode": {"type": "string", "enum": ["safe", "fast"]},
    },
    "required": ["count", "mode"],
    "additionalProperties": False,
}


def test_public_specs_expose_contract_but_not_callable():
    specs = public_tool_specs(REGISTRY)

    assert {spec["name"] for spec in specs} == set(REGISTRY)
    assert all("fn" not in spec for spec in specs)
    specs[0]["input_schema"]["required"].clear()
    assert REGISTRY[specs[0]["name"]].schema["required"]


def test_validate_args_accepts_declared_values():
    assert validate_args({"count": 2, "mode": "safe"}, STRICT_SCHEMA) == []


def test_validate_args_rejects_missing_type_enum_extra_and_bool():
    assert "нет обязательного аргумента: mode" in validate_args(
        {"count": 2}, STRICT_SCHEMA
    )
    assert "count: ожидался integer" in validate_args(
        {"count": "2", "mode": "safe"}, STRICT_SCHEMA
    )
    assert "mode: значение не входит в enum [safe, fast]" in validate_args(
        {"count": 2, "mode": "unsafe"}, STRICT_SCHEMA
    )
    assert "неизвестный аргумент: debug" in validate_args(
        {"count": 2, "mode": "safe", "debug": True}, STRICT_SCHEMA
    )
    assert "count: ожидался integer" in validate_args(
        {"count": True, "mode": "safe"}, STRICT_SCHEMA
    )


def test_dispatch_executes_allowlisted_tool_and_links_result():
    result = dispatch(
        {
            "type": "tool_call",
            "id": "call-add-1",
            "name": "add",
            "arguments": {"a": 2, "b": 3},
        },
        REGISTRY,
    )

    assert result == {
        "type": "tool_result",
        "call_id": "call-add-1",
        "ok": True,
        "content": 5,
    }


def test_dispatch_rejects_invalid_call_before_execution():
    executed = []
    registry = {
        "record": Tool(
            "record",
            "Записать значение.",
            {
                "type": "object",
                "properties": {"value": {"type": "string"}},
                "required": ["value"],
                "additionalProperties": False,
            },
            lambda value: executed.append(value),
        )
    }

    with pytest.raises(ToolError, match="обязательного аргумента"):
        dispatch(
            {
                "type": "tool_call",
                "id": "call-record-1",
                "name": "record",
                "arguments": {},
            },
            registry,
        )

    assert executed == []


def test_dispatch_rejects_unknown_tool():
    with pytest.raises(ToolError, match="неизвестный инструмент"):
        dispatch(
            {
                "type": "tool_call",
                "id": "call-unknown-1",
                "name": "delete_everything",
                "arguments": {},
            },
            REGISTRY,
        )


def test_run_passes_user_request_and_public_specs():
    observed = {}

    def model(history, tool_specs):
        observed["history"] = history
        observed["tool_specs"] = tool_specs
        return {"type": "final", "answer": "готово"}

    answer, trace = run(model, REGISTRY, "Сложи два числа")

    assert answer == "готово"
    assert observed["history"] == [
        {"type": "user", "content": "Сложи два числа"}
    ]
    assert all("fn" not in spec for spec in observed["tool_specs"])
    assert trace[-1] == {"type": "final", "answer": "готово"}


def test_run_records_call_result_and_final_in_order():
    answer, trace = run(_demo_model, REGISTRY, DEMO_REQUEST)

    assert answer == "Решение: publish для paid_revenue на 2026-07-01."
    assert [event["type"] for event in trace] == [
        "user",
        "tool_call",
        "tool_result",
        "final",
    ]
    assert trace[1]["id"] == trace[2]["call_id"] == "call-release-1"
    assert trace[2]["ok"] is True


def test_run_returns_validation_error_to_model_and_allows_repair():
    executed = []
    registry = {
        "lookup": Tool(
            "lookup",
            "Найти статус по item_id.",
            {
                "type": "object",
                "properties": {
                    "item_id": {"type": "string", "enum": ["item-1"]}
                },
                "required": ["item_id"],
                "additionalProperties": False,
            },
            lambda item_id: executed.append(item_id) or "ready",
        )
    }

    def repairing_model(history, _tool_specs):
        results = [event for event in history if event["type"] == "tool_result"]
        if not results:
            return {
                "type": "tool_call",
                "id": "call-bad",
                "name": "lookup",
                "arguments": {},
            }
        if results[-1]["ok"] is False:
            return {
                "type": "tool_call",
                "id": "call-fixed",
                "name": "lookup",
                "arguments": {"item_id": "item-1"},
            }
        return {"type": "final", "answer": results[-1]["content"]}

    answer, trace = run(
        repairing_model, registry, "Проверь item-1", max_tool_calls=2
    )

    results = [event for event in trace if event["type"] == "tool_result"]
    assert answer == "ready"
    assert executed == ["item-1"]
    assert [(result["call_id"], result["ok"]) for result in results] == [
        ("call-bad", False),
        ("call-fixed", True),
    ]


def test_run_rejects_unknown_model_envelope():
    def broken_model(_history, _tool_specs):
        return {"type": "message", "content": "готово"}

    with pytest.raises(ToolError, match="tool_call или type=final"):
        run(broken_model, REGISTRY, "Сложи два числа")


def test_run_stops_before_call_beyond_budget():
    executed = []
    registry = {
        "ping": Tool(
            "ping",
            "Вернуть pong.",
            {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            lambda: executed.append("ping") or "pong",
        )
    }

    def looping_model(history, _tool_specs):
        calls = [event for event in history if event["type"] == "tool_call"]
        return {
            "type": "tool_call",
            "id": f"call-{len(calls) + 1}",
            "name": "ping",
            "arguments": {},
        }

    with pytest.raises(ToolError, match="max_tool_calls"):
        run(looping_model, registry, "Продолжай", max_tool_calls=2)

    assert executed == ["ping", "ping"]
