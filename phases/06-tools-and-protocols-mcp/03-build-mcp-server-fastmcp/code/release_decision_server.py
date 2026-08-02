"""Reference MCP server for lesson 6.3.

The server exposes one read-only capability over a safe in-memory fixture. The MCP
Python SDK owns protocol discovery, schemas, validation and result envelopes; this
module owns the domain boundary and the handler's behaviour.
"""

import asyncio
from typing import Literal, TypedDict

from mcp import Client
from mcp.server import MCPServer
from mcp.types import ToolAnnotations


class ReleaseDecision(TypedDict):
    """Structured result returned for one recorded quality-gate run."""

    run_id: str
    decision: Literal["publish", "review", "block"]
    reason: str


RELEASE_DECISIONS: dict[str, ReleaseDecision] = {
    "phase-5-paid-revenue-q2": {
        "run_id": "phase-5-paid-revenue-q2",
        "decision": "publish",
        "reason": "All required checks passed on the recorded local fixture.",
    },
    "phase-5-orders-anomaly": {
        "run_id": "phase-5-orders-anomaly",
        "decision": "review",
        "reason": "The anomaly check needs a human decision before publication.",
    },
}


def lookup_release_decision(run_id: str) -> ReleaseDecision:
    """Read one decision from the local domain fixture."""

    try:
        return RELEASE_DECISIONS[run_id].copy()
    except KeyError:
        raise ValueError(f"Unknown run_id: {run_id}") from None


mcp = MCPServer("analytics-quality")


@mcp.tool(
    title="Get release decision",
    annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False),
)
def get_release_decision(run_id: str) -> ReleaseDecision:
    """Return the recorded quality-gate decision for one local run ID."""

    return lookup_release_decision(run_id)


async def _demo() -> None:
    """Exercise the server through the same in-memory client used by tests."""

    async with Client(mcp, raise_exceptions=True) as client:
        listed = await client.list_tools()
        print("tools:", [tool.name for tool in listed.tools])

        result = await client.call_tool(
            "get_release_decision",
            {"run_id": "phase-5-paid-revenue-q2"},
        )
        print("result:", result.structured_content)


if __name__ == "__main__":
    asyncio.run(_demo())
