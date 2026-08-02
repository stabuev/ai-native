"""Reference MCP server with an explicit server-side access policy.

The model supplies only the domain argument ``run_id``. Actor, scopes and object
boundaries come from trusted deployment configuration and cannot be selected through
tool arguments. The access decision is made inside the public MCP capability before the
domain adapter is called.
"""

import asyncio
from dataclasses import dataclass
from typing import Literal, TypedDict

from mcp import Client
from mcp.server import MCPServer
from mcp.types import ToolAnnotations


READ_RELEASE_SCOPE = "release_decision:read"
CAPABILITY_NAME = "get_release_decision"
DENIED_MESSAGE = "Access denied by server policy."


class ReleaseDecision(TypedDict):
    """Structured result returned for one recorded quality-gate run."""

    run_id: str
    decision: Literal["publish", "review", "block"]
    reason: str


class AccessEvent(TypedDict):
    """Minimal audit event for an authorization decision, not an execution result."""

    actor: str
    capability: str
    object_ref: str
    allowed: bool
    reason_code: Literal["policy_match", "missing_scope", "object_out_of_scope"]


@dataclass(frozen=True)
class AccessContext:
    """Trusted context configured by the server operator, never by tool arguments."""

    actor: str
    scopes: frozenset[str]
    allowed_run_ids: frozenset[str]


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


DEFAULT_LOCAL_ACCESS = AccessContext(
    actor="local-course-operator",
    scopes=frozenset({READ_RELEASE_SCOPE}),
    allowed_run_ids=frozenset({"phase-5-paid-revenue-q2"}),
)

# For the local STDIO reference route this is trusted startup configuration. A remote
# HTTP deployment must build the same shape from a verified token/context in trusted
# middleware rather than from model-controlled tool arguments.
LOCAL_ACCESS = DEFAULT_LOCAL_ACCESS

# An in-memory sink keeps the example observable. Production code should emit structured
# events to a protected logger and add a server-generated correlation ID and timestamp.
AUDIT_EVENTS: list[AccessEvent] = []


def lookup_release_decision(run_id: str) -> ReleaseDecision:
    """Read one decision from the local domain fixture."""

    try:
        return RELEASE_DECISIONS[run_id].copy()
    except KeyError:
        raise ValueError(f"Unknown run_id: {run_id}") from None


def _record_access_decision(
    context: AccessContext,
    run_id: str,
    *,
    allowed: bool,
    reason_code: Literal["policy_match", "missing_scope", "object_out_of_scope"],
) -> None:
    """Record only the fields needed to explain an access decision."""

    AUDIT_EVENTS.append(
        {
            "actor": context.actor,
            "capability": CAPABILITY_NAME,
            "object_ref": run_id,
            "allowed": allowed,
            "reason_code": reason_code,
        }
    )


def require_release_access(context: AccessContext, run_id: str) -> None:
    """Authorize one action and object before the domain adapter is entered."""

    if READ_RELEASE_SCOPE not in context.scopes:
        _record_access_decision(
            context,
            run_id,
            allowed=False,
            reason_code="missing_scope",
        )
        raise PermissionError(DENIED_MESSAGE)

    if run_id not in context.allowed_run_ids:
        _record_access_decision(
            context,
            run_id,
            allowed=False,
            reason_code="object_out_of_scope",
        )
        raise PermissionError(DENIED_MESSAGE)

    _record_access_decision(
        context,
        run_id,
        allowed=True,
        reason_code="policy_match",
    )


mcp = MCPServer("analytics-quality-secured")


@mcp.tool(
    title="Get release decision",
    annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False),
)
def get_release_decision(run_id: str) -> ReleaseDecision:
    """Return one recorded release decision visible to this server deployment."""

    require_release_access(LOCAL_ACCESS, run_id)
    return lookup_release_decision(run_id)


async def _demo() -> None:
    """Show one allowed and one denied call through a real in-memory MCP client."""

    AUDIT_EVENTS.clear()
    async with Client(mcp, raise_exceptions=True) as client:
        allowed = await client.call_tool(
            CAPABILITY_NAME,
            {"run_id": "phase-5-paid-revenue-q2"},
        )
        denied = await client.call_tool(
            CAPABILITY_NAME,
            {"run_id": "phase-5-orders-anomaly"},
        )

    print("allowed:", allowed.structured_content)
    print("denied:", denied.is_error)
    print("audit:", AUDIT_EVENTS)


if __name__ == "__main__":
    asyncio.run(_demo())
