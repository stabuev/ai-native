"""Offline preflight for transferring Phase 4 artifacts into an agent runtime.

The module does not call a model, execute a tool, install a platform, or pretend to
implement an agent loop. It makes a deployment decision observable: what will be
loaded, which permissions are missing, and where selected data may leave the host.
"""

import json
import time


def _unique(values, label):
    """Validate a string list and return sorted unique values."""
    if values is None:
        return []
    if not isinstance(values, list):
        raise ValueError(f"{label} must be a list")
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError(f"{label} must contain non-empty strings")
    return sorted(set(value.strip() for value in values))


def _require_text(mapping, key, label):
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}.{key} must be a non-empty string")
    return value.strip()


def prepare_run(skill, project, memories, context_manifest, runtime, now=None):
    """Build a reproducible readiness report for one planned agent run.

    The inputs are summaries of artifacts created in lessons 4.1–4.4:

    - skill: validated SKILL.md metadata and its runtime requirements;
    - project: scope, permissions, memory owner, and acceptance scenarios;
    - memories: only governed records that may be referenced by the manifest;
    - context_manifest: the kept/dropped decision produced by lesson 4.4;
    - runtime: available capabilities and declared external connections.

    Operational mismatches become blockers in the report. Structurally malformed
    input raises ValueError because no reliable preflight can be built from it.
    """
    for value, label in (
        (skill, "skill"),
        (project, "project"),
        (context_manifest, "context_manifest"),
        (runtime, "runtime"),
    ):
        if not isinstance(value, dict):
            raise ValueError(f"{label} must be a mapping")
    if not isinstance(memories, list):
        raise ValueError("memories must be a list")

    skill_name = _require_text(skill, "name", "skill")
    project_name = _require_text(project, "name", "project")
    runtime_name = _require_text(runtime, "name", "runtime")

    kept = context_manifest.get("kept")
    dropped = context_manifest.get("dropped")
    if not isinstance(kept, list) or not isinstance(dropped, list):
        raise ValueError("context_manifest.kept and .dropped must be lists")

    kept_ids = []
    for item in kept:
        if not isinstance(item, dict):
            raise ValueError("every kept context item must be a mapping")
        kept_ids.append(_require_text(item, "id", "context_manifest.kept item"))
        _require_text(item, "source", "context_manifest.kept item")
    if len(kept_ids) != len(set(kept_ids)):
        raise ValueError("kept context ids must be unique")

    used_units = context_manifest.get("used_units")
    input_budget_units = context_manifest.get("input_budget_units")
    reserve_units = context_manifest.get("reserve_units")
    if not all(isinstance(value, int) and value >= 0 for value in (used_units, input_budget_units, reserve_units)):
        raise ValueError("context budget values must be non-negative integers")

    blockers = []
    if used_units > input_budget_units:
        blockers.append("context_budget_exceeded")

    required_context_ids = _unique(
        project.get("required_context_ids"),
        "project.required_context_ids",
    )
    for item_id in required_context_ids:
        if item_id not in kept_ids:
            blockers.append(f"required_context_missing:{item_id}")

    required_tools = _unique(skill.get("required_tools"), "skill.required_tools")
    allowed_tools = _unique(project.get("allowed_tools"), "project.allowed_tools")
    available_tools = _unique(
        runtime.get("available_tools"),
        "runtime.available_tools",
    )
    usable_tools = sorted(set(allowed_tools) & set(available_tools))
    missing_tools = sorted(set(required_tools) - set(usable_tools))
    blockers.extend(f"missing_tool:{name}" for name in missing_tools)

    required_secrets = _unique(
        skill.get("required_secrets"),
        "skill.required_secrets",
    )
    available_secrets = _unique(
        runtime.get("available_secrets"),
        "runtime.available_secrets",
    )
    missing_secrets = sorted(set(required_secrets) - set(available_secrets))
    blockers.extend(f"missing_secret:{name}" for name in missing_secrets)

    memory_by_id = {}
    for record in memories:
        if not isinstance(record, dict):
            raise ValueError("every memory record must be a mapping")
        record_id = _require_text(record, "id", "memory record")
        if record_id in memory_by_id:
            raise ValueError("memory ids must be unique")
        memory_by_id[record_id] = record

    selected_memory_ids = [item["id"] for item in kept if item["source"] == "memory"]
    expected_owner = project.get("memory_owner")
    current_time = time.time() if now is None else float(now)
    for record_id in selected_memory_ids:
        record = memory_by_id.get(record_id)
        if record is None:
            blockers.append(f"memory_record_missing:{record_id}")
            continue
        if expected_owner and record.get("owner") != expected_owner:
            blockers.append(f"memory_owner_mismatch:{record_id}")
        if not record.get("active", False):
            blockers.append(f"memory_inactive:{record_id}")
        expires_at = record.get("expires_at")
        if expires_at is not None and float(expires_at) <= current_time:
            blockers.append(f"memory_expired:{record_id}")

    approved_external = set(
        _unique(
            project.get("approved_external_connections"),
            "project.approved_external_connections",
        )
    )
    connections = runtime.get("connections") or []
    if not isinstance(connections, list):
        raise ValueError("runtime.connections must be a list")
    data_egress = []
    for connection in connections:
        if not isinstance(connection, dict):
            raise ValueError("every runtime connection must be a mapping")
        connection_name = _require_text(connection, "name", "runtime connection")
        connection_kind = _require_text(connection, "kind", "runtime connection")
        if connection.get("external", False):
            data_egress.append(
                {
                    "name": connection_name,
                    "kind": connection_kind,
                    "sends": _unique(
                        connection.get("sends"),
                        "runtime connection.sends",
                    ),
                }
            )
            if connection_name not in approved_external:
                blockers.append(f"external_connection_not_approved:{connection_name}")

    report = {
        "status": "blocked" if blockers else "ready",
        "mapping": {
            "skill": skill_name,
            "project": project_name,
            "runtime": runtime_name,
            "context_ids": kept_ids,
            "memory_ids": selected_memory_ids,
        },
        "context": {
            "used_units": used_units,
            "input_budget_units": input_budget_units,
            "reserve_units": reserve_units,
            "dropped": [
                {"id": item.get("id"), "reason": item.get("reason")}
                for item in dropped
            ],
        },
        "permissions": {
            "required_tools": required_tools,
            "allowed_tools": allowed_tools,
            "available_tools": available_tools,
            "missing_tools": missing_tools,
            "required_secret_names": required_secrets,
            "missing_secret_names": missing_secrets,
        },
        "data_egress": data_egress,
        "acceptance_scenarios": _unique(
            project.get("acceptance_scenarios"),
            "project.acceptance_scenarios",
        ),
        "blockers": blockers,
    }
    return report


DEMO_SKILL = {
    "name": "returns-answer-review",
    "description": "Проверяет ответ по действующей политике возвратов",
    "required_tools": ["knowledge.read"],
    "required_secrets": [],
}

DEMO_PROJECT = {
    "name": "returns-assistant",
    "required_context_ids": ["instructions", "request"],
    "allowed_tools": ["knowledge.read"],
    "memory_owner": "support-project",
    "approved_external_connections": [],
    "acceptance_scenarios": ["P-01", "P-02", "P-03", "P-04", "P-05", "P-06"],
}

DEMO_MEMORIES = [
    {
        "id": "format-preference",
        "owner": "support-project",
        "active": True,
        "expires_at": None,
    }
]

DEMO_CONTEXT_MANIFEST = {
    "kept": [
        {
            "id": "instructions",
            "source": "project",
            "content": "Отвечай только по действующей политике.",
            "required": True,
            "relevance": 3,
            "units": 5,
        },
        {
            "id": "request",
            "source": "user",
            "content": "Какой сейчас срок возврата товара?",
            "required": True,
            "relevance": 3,
            "units": 5,
        },
        {
            "id": "policy-v2",
            "source": "rag",
            "content": "Действующая политика: возврат возможен в течение тридцати дней.",
            "required": False,
            "relevance": 3,
            "units": 8,
        },
        {
            "id": "format-preference",
            "source": "memory",
            "content": "Пользователь предпочитает краткий ответ.",
            "required": False,
            "relevance": 2,
            "units": 4,
        },
    ],
    "dropped": [
        {
            "id": "history-summary",
            "source": "history",
            "content": "Решение: показать итог таблицей. Проверили черновик.",
            "required": False,
            "relevance": 1,
            "units": 6,
            "reason": "budget",
        },
        {
            "id": "policy-v1",
            "source": "rag",
            "content": "Архивная политика: возврат возможен в течение четырнадцати дней.",
            "required": False,
            "relevance": 0,
            "units": 8,
            "reason": "not_relevant",
        },
    ],
    "used_units": 22,
    "input_budget_units": 24,
    "reserve_units": 6,
}

DEMO_RUNTIME = {
    "name": "offline-preflight",
    "available_tools": ["knowledge.read"],
    "available_secrets": [],
    "connections": [
        {
            "name": "local-model",
            "kind": "model",
            "external": False,
            "sends": ["request", "selected_context"],
        }
    ],
}


if __name__ == "__main__":
    print(
        json.dumps(
            prepare_run(
                DEMO_SKILL,
                DEMO_PROJECT,
                DEMO_MEMORIES,
                DEMO_CONTEXT_MANIFEST,
                DEMO_RUNTIME,
                now=1_800_000_000,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )
