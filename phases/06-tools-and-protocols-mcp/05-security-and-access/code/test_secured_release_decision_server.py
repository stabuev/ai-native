"""Behavioural specification for access control integrated into the MCP capability."""

import pytest
from mcp import Client

import secured_release_decision_server as server_module


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def reset_access_state(monkeypatch: pytest.MonkeyPatch):
    server_module.AUDIT_EVENTS.clear()
    monkeypatch.setattr(
        server_module,
        "LOCAL_ACCESS",
        server_module.DEFAULT_LOCAL_ACCESS,
    )


@pytest.fixture
async def client():
    async with Client(server_module.mcp, raise_exceptions=True) as connected:
        yield connected


def _result_text(result) -> str:
    return "\n".join(
        block.text for block in result.content if getattr(block, "type", None) == "text"
    )


@pytest.mark.anyio
async def test_public_schema_does_not_let_the_model_choose_identity_or_scope(
    client: Client,
):
    listed = await client.list_tools()
    tool = next(tool for tool in listed.tools if tool.name == server_module.CAPABILITY_NAME)

    assert set(tool.input_schema["properties"]) == {"run_id"}
    assert tool.input_schema["required"] == ["run_id"]
    assert {"actor", "principal", "role", "scope", "scopes"}.isdisjoint(
        tool.input_schema["properties"]
    )


@pytest.mark.anyio
async def test_allowed_action_and_object_return_the_domain_result(client: Client):
    result = await client.call_tool(
        server_module.CAPABILITY_NAME,
        {"run_id": "phase-5-paid-revenue-q2"},
    )

    assert result.is_error is False
    assert result.structured_content == {
        "run_id": "phase-5-paid-revenue-q2",
        "decision": "publish",
        "reason": "All required checks passed on the recorded local fixture.",
    }
    assert server_module.AUDIT_EVENTS == [
        {
            "actor": "local-course-operator",
            "capability": "get_release_decision",
            "object_ref": "phase-5-paid-revenue-q2",
            "allowed": True,
            "reason_code": "policy_match",
        }
    ]


@pytest.mark.anyio
async def test_missing_scope_is_denied_before_domain_lookup(
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        server_module,
        "LOCAL_ACCESS",
        server_module.AccessContext(
            actor="local-course-operator",
            scopes=frozenset(),
            allowed_run_ids=frozenset({"phase-5-paid-revenue-q2"}),
        ),
    )

    called = False

    def fail_if_called(run_id: str):
        nonlocal called
        called = True
        raise AssertionError(f"lookup must not run after denied access: {run_id}")

    monkeypatch.setattr(server_module, "lookup_release_decision", fail_if_called)
    result = await client.call_tool(
        server_module.CAPABILITY_NAME,
        {"run_id": "phase-5-paid-revenue-q2"},
    )

    assert result.is_error is True
    assert called is False
    assert server_module.DENIED_MESSAGE in _result_text(result)
    assert server_module.AUDIT_EVENTS[-1]["reason_code"] == "missing_scope"


@pytest.mark.anyio
async def test_existing_but_out_of_scope_object_is_denied_before_lookup(
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
):
    called = False

    def fail_if_called(run_id: str):
        nonlocal called
        called = True
        raise AssertionError(f"lookup must not run for out-of-scope object: {run_id}")

    monkeypatch.setattr(server_module, "lookup_release_decision", fail_if_called)
    result = await client.call_tool(
        server_module.CAPABILITY_NAME,
        {"run_id": "phase-5-orders-anomaly"},
    )

    assert result.is_error is True
    assert called is False
    assert server_module.DENIED_MESSAGE in _result_text(result)
    assert "phase-5-orders-anomaly" not in _result_text(result)
    assert server_module.AUDIT_EVENTS[-1]["reason_code"] == "object_out_of_scope"


@pytest.mark.anyio
async def test_model_supplied_actor_and_scopes_cannot_replace_trusted_context(
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
):
    observed = {}

    def capture_context(context, run_id):
        observed["context"] = context
        observed["run_id"] = run_id

    monkeypatch.setattr(server_module, "require_release_access", capture_context)
    result = await client.call_tool(
        server_module.CAPABILITY_NAME,
        {
            "run_id": "phase-5-paid-revenue-q2",
            "actor": "admin",
            "scopes": ["*"],
        },
    )

    assert result.is_error is False
    assert observed == {
        "context": server_module.DEFAULT_LOCAL_ACCESS,
        "run_id": "phase-5-paid-revenue-q2",
    }
    assert server_module.AUDIT_EVENTS == []
