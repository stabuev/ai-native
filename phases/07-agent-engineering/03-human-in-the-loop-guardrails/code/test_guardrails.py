import pytest
from guardrails import run_action, requires_confirmation, amount_limit, GuardrailError

TOOLS = {
    "read": lambda **k: "данные",
    "delete": lambda **k: "удалено",
    "send_money": lambda amount, to: f"{amount}->{to}",
}


def test_safe_action_runs_without_confirmation():
    assert run_action({"tool": "read", "args": {}}, TOOLS) == "данные"


def test_dangerous_requires_confirmation():
    assert requires_confirmation("delete")
    with pytest.raises(GuardrailError):
        run_action({"tool": "delete", "args": {}}, TOOLS)            # без confirm
    assert run_action({"tool": "delete", "args": {}}, TOOLS, confirm=lambda a: True) == "удалено"


def test_denied_confirmation_blocks():
    with pytest.raises(GuardrailError):
        run_action({"tool": "delete", "args": {}}, TOOLS, confirm=lambda a: False)


def test_validator_blocks_out_of_bounds():
    with pytest.raises(GuardrailError):
        run_action({"tool": "send_money", "args": {"amount": 500, "to": "X"}},
                   TOOLS, confirm=lambda a: True, validators=[amount_limit(100)])
    ok = run_action({"tool": "send_money", "args": {"amount": 50, "to": "X"}},
                    TOOLS, confirm=lambda a: True, validators=[amount_limit(100)])
    assert ok == "50->X"


def test_unknown_tool_blocked():
    with pytest.raises(GuardrailError):
        run_action({"tool": "nope", "args": {}}, TOOLS)
