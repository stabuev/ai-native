import pytest
from function_calling import validate_args, dispatch, run, ToolError, REGISTRY, _demo_model

SCHEMA = {"properties": {"a": {"type": "number"}, "b": {"type": "number"}}, "required": ["a", "b"]}


def test_validate_args_missing_and_type():
    assert "нет обязательного аргумента: b" in validate_args({"a": 1}, SCHEMA)
    assert any("ожидался number" in e for e in validate_args({"a": "x", "b": 2}, SCHEMA))
    assert validate_args({"a": 1, "b": 2}, SCHEMA) == []


def test_dispatch_executes_tool():
    assert dispatch({"name": "add", "arguments": {"a": 2, "b": 3}}, REGISTRY) == 5


def test_dispatch_unknown_tool_raises():
    with pytest.raises(ToolError):
        dispatch({"name": "nope", "arguments": {}}, REGISTRY)


def test_dispatch_invalid_args_raises():
    with pytest.raises(ToolError):
        dispatch({"name": "add", "arguments": {"a": 1}}, REGISTRY)   # нет b


def test_run_loop_uses_tool_result_for_final():
    answer, history = run(_demo_model, REGISTRY)
    assert answer == 5
    assert len(history) == 1
    assert history[0]["call"]["name"] == "add"
