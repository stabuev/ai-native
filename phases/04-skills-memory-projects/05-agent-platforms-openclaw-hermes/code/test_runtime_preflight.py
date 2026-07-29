from copy import deepcopy

import pytest

from runtime_preflight import (
    DEMO_CONTEXT_MANIFEST,
    DEMO_MEMORY_SNAPSHOT,
    DEMO_PROJECT,
    DEMO_RUNTIME,
    DEMO_SKILL,
    prepare_run,
)


NOW = 1_800_000_000


def _inputs():
    return (
        deepcopy(DEMO_SKILL),
        deepcopy(DEMO_PROJECT),
        deepcopy(DEMO_MEMORY_SNAPSHOT),
        deepcopy(DEMO_CONTEXT_MANIFEST),
        deepcopy(DEMO_RUNTIME),
    )


def test_ready_report_maps_all_phase_artifacts():
    report = prepare_run(*_inputs(), now=NOW)

    assert report["status"] == "ready"
    assert report["mapping"] == {
        "skill": "returns-answer-review",
        "project": "returns-assistant",
        "runtime": "offline-preflight",
        "context_ids": [
            "instructions",
            "request",
            "policy-v2",
            "format-preference",
        ],
        "memory_refs": [
            {
                "context_id": "format-preference",
                "owner": "support-project",
                "key": "response.format",
                "record_id": 0,
            }
        ],
    }
    assert report["context"]["dropped"] == [
        {"id": "history-summary", "reason": "budget"},
        {"id": "policy-v1", "reason": "not_relevant"},
    ]
    assert report["blockers"] == []


def test_missing_runtime_capability_blocks_the_run():
    skill, project, memory_snapshot, manifest, runtime = _inputs()
    runtime["available_tools"] = []

    report = prepare_run(
        skill,
        project,
        memory_snapshot,
        manifest,
        runtime,
        now=NOW,
    )

    assert report["status"] == "blocked"
    assert report["permissions"]["missing_tools"] == ["knowledge.read"]
    assert "missing_tool:knowledge.read" in report["blockers"]


def test_required_context_cannot_disappear_or_exceed_budget():
    skill, project, memory_snapshot, manifest, runtime = _inputs()
    manifest["kept"] = [
        item for item in manifest["kept"] if item["id"] != "instructions"
    ]
    manifest["used_units"] = 25

    report = prepare_run(
        skill,
        project,
        memory_snapshot,
        manifest,
        runtime,
        now=NOW,
    )

    assert report["status"] == "blocked"
    assert "required_context_missing:instructions" in report["blockers"]
    assert "context_budget_exceeded" in report["blockers"]


def test_expired_or_wrong_owner_memory_blocks_the_run():
    skill, project, memory_snapshot, manifest, runtime = _inputs()
    memory_snapshot["owner"] = "another-project"
    memory_snapshot["items"][0]["expires_at"] = NOW

    report = prepare_run(
        skill,
        project,
        memory_snapshot,
        manifest,
        runtime,
        now=NOW,
    )

    assert report["status"] == "blocked"
    assert "memory_owner_mismatch:format-preference" in report["blockers"]
    assert "memory_expired:format-preference" in report["blockers"]


def test_external_data_path_is_visible_and_requires_approval():
    skill, project, memory_snapshot, manifest, runtime = _inputs()
    runtime["connections"].append(
        {
            "name": "cloud-model",
            "kind": "model",
            "external": True,
            "sends": ["request", "selected_context"],
        }
    )

    blocked = prepare_run(
        skill,
        project,
        memory_snapshot,
        manifest,
        runtime,
        now=NOW,
    )
    assert blocked["data_egress"] == [
        {
            "name": "cloud-model",
            "kind": "model",
            "sends": ["request", "selected_context"],
        }
    ]
    assert "external_connection_not_approved:cloud-model" in blocked["blockers"]

    project["approved_external_connections"] = ["cloud-model"]
    ready = prepare_run(
        skill,
        project,
        memory_snapshot,
        manifest,
        runtime,
        now=NOW,
    )
    assert ready["status"] == "ready"


def test_malformed_artifact_fails_before_a_misleading_report():
    skill, project, memory_snapshot, manifest, runtime = _inputs()
    skill["name"] = ""

    with pytest.raises(ValueError, match="skill.name"):
        prepare_run(
            skill,
            project,
            memory_snapshot,
            manifest,
            runtime,
            now=NOW,
        )

    skill["name"] = "returns-answer-review"
    skill["required_tools"] = "knowledge.read"
    with pytest.raises(ValueError, match="skill.required_tools"):
        prepare_run(
            skill,
            project,
            memory_snapshot,
            manifest,
            runtime,
            now=NOW,
        )


def test_memory_manifest_reference_must_match_snapshot_record():
    skill, project, memory_snapshot, manifest, runtime = _inputs()
    memory_item = next(
        item for item in manifest["kept"] if item["source"] == "memory"
    )
    memory_item["source_ref"]["key"] = "another.key"

    report = prepare_run(
        skill,
        project,
        memory_snapshot,
        manifest,
        runtime,
        now=NOW,
    )

    assert report["status"] == "blocked"
    assert "memory_key_mismatch:format-preference" in report["blockers"]
