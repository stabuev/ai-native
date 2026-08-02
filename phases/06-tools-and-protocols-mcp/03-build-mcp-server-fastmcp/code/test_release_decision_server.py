"""Behavioural specification for the reference MCP server in lesson 6.3."""

import pytest
from mcp import Client

import release_decision_server as server_module


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with Client(server_module.mcp, raise_exceptions=True) as connected:
        yield connected


def _result_text(result) -> str:
    return "\n".join(
        block.text for block in result.content if getattr(block, "type", None) == "text"
    )


@pytest.mark.anyio
async def test_descriptor_is_generated_from_public_contract(client: Client):
    listed = await client.list_tools()
    tool = next(tool for tool in listed.tools if tool.name == "get_release_decision")

    assert tool.description == "Return the recorded quality-gate decision for one local run ID."
    assert tool.input_schema["properties"]["run_id"]["type"] == "string"
    assert tool.input_schema["required"] == ["run_id"]
    assert {"run_id", "decision", "reason"} <= set(tool.output_schema["properties"])


@pytest.mark.anyio
async def test_valid_call_returns_structured_domain_result(client: Client):
    result = await client.call_tool(
        "get_release_decision",
        {"run_id": "phase-5-paid-revenue-q2"},
    )

    assert result.is_error is False
    assert result.structured_content == {
        "run_id": "phase-5-paid-revenue-q2",
        "decision": "publish",
        "reason": "All required checks passed on the recorded local fixture.",
    }


@pytest.mark.anyio
async def test_invalid_arguments_are_rejected_before_domain_lookup(
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_if_called(run_id: str):
        raise AssertionError(f"domain lookup must not run for invalid input: {run_id}")

    monkeypatch.setattr(server_module, "lookup_release_decision", fail_if_called)
    result = await client.call_tool("get_release_decision", {})

    assert result.is_error is True
    assert "run_id" in _result_text(result)


@pytest.mark.anyio
async def test_unknown_run_is_a_recoverable_tool_error(client: Client):
    result = await client.call_tool(
        "get_release_decision",
        {"run_id": "missing-run"},
    )

    assert result.is_error is True
    assert result.structured_content is None
    assert "Unknown run_id: missing-run" in _result_text(result)
