import asyncio
import importlib.util
from pathlib import Path
import sys

import pytest


pytest.importorskip("mcp")

from mcp import Client


ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / "phases/06-tools-and-protocols-mcp"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_release_decision_contract_survives_tool_mcp_and_access_control():
    tool_runtime = _load_module(
        "phase6_tool_runtime",
        PHASE / "01-tool-use-function-calling/code/function_calling.py",
    )
    server = _load_module(
        "phase6_mcp_server",
        PHASE / "03-build-mcp-server-fastmcp/code/release_decision_server.py",
    )
    secured = _load_module(
        "phase6_secured_server",
        PHASE
        / "05-security-and-access/code/secured_release_decision_server.py",
    )

    public_spec = next(
        spec
        for spec in tool_runtime.public_tool_specs(tool_runtime.REGISTRY)
        if spec["name"] == "get_release_decision"
    )
    assert public_spec["input_schema"]["required"] == ["run_id"]
    assert set(public_spec["input_schema"]["properties"]) == {"run_id"}

    async def exercise_servers():
        async with Client(server.mcp, raise_exceptions=True) as client:
            listed = await client.list_tools()
            descriptor = next(
                tool for tool in listed.tools if tool.name == "get_release_decision"
            )
            unprotected = await client.call_tool(
                "get_release_decision",
                {"run_id": "phase-5-paid-revenue-q2"},
            )

        secured.AUDIT_EVENTS.clear()
        async with Client(secured.mcp, raise_exceptions=True) as client:
            secured_listed = await client.list_tools()
            secured_descriptor = next(
                tool
                for tool in secured_listed.tools
                if tool.name == secured.CAPABILITY_NAME
            )
            allowed = await client.call_tool(
                secured.CAPABILITY_NAME,
                {"run_id": "phase-5-paid-revenue-q2"},
            )
            denied = await client.call_tool(
                secured.CAPABILITY_NAME,
                {"run_id": "phase-5-orders-anomaly"},
            )

        return descriptor, secured_descriptor, unprotected, allowed, denied

    descriptor, secured_descriptor, unprotected, allowed, denied = asyncio.run(
        exercise_servers()
    )

    assert descriptor.input_schema["required"] == ["run_id"]
    assert secured_descriptor.input_schema["required"] == ["run_id"]
    assert set(secured_descriptor.input_schema["properties"]) == {"run_id"}
    assert unprotected.structured_content == allowed.structured_content
    assert allowed.structured_content["decision"] == "publish"
    assert denied.is_error is True
    assert secured.AUDIT_EVENTS[-1]["reason_code"] == "object_out_of_scope"
