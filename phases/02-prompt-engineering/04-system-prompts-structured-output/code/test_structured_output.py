import json

import pytest

from structured_output import (
    OUTPUT_SCHEMA,
    SOURCE_NOTES,
    finish_semantic_review,
    inspect_response,
    validate_evidence,
    validate_structure,
)


def completed(data):
    return {
        "status": "completed",
        "output_text": json.dumps(data, ensure_ascii=False),
    }


def fact(**changes):
    value = {
        "category": "decision",
        "statement": "Пилот запускается для 10% пользователей iOS.",
        "evidence": "для 10% пользователей iOS",
        "owner": None,
        "deadline": "18 сентября",
    }
    value.update(changes)
    return value


def test_output_schema_is_real_closed_json_schema():
    assert OUTPUT_SCHEMA["type"] == "object"
    assert OUTPUT_SCHEMA["required"] == ["facts"]
    assert OUTPUT_SCHEMA["additionalProperties"] is False
    item_schema = OUTPUT_SCHEMA["properties"]["facts"]["items"]
    assert set(item_schema["required"]) == {
        "category",
        "statement",
        "evidence",
        "owner",
        "deadline",
    }
    assert item_schema["additionalProperties"] is False


@pytest.mark.parametrize(
    "response",
    [
        {"status": "refusal", "reason": "safety policy"},
        {"status": "incomplete", "reason": "max_output_tokens"},
    ],
)
def test_non_completed_response_stops_before_parsing(response):
    report = inspect_response(response, SOURCE_NOTES)
    assert report["decision"] == "stop"
    assert report["stage"] == "status"
    assert report["data"] is None


def test_fenced_prompt_only_json_is_rejected_at_syntax_gate():
    response = {
        "status": "completed",
        "output_text": '```json\n{"facts": []}\n```',
    }
    report = inspect_response(response, SOURCE_NOTES)
    assert report["decision"] == "stop"
    assert report["stage"] == "syntax"


def test_structure_gate_reports_missing_extra_and_domain_errors():
    invalid = {
        "facts": [
            {
                "category": "plan",
                "statement": "Запустить пилот.",
                "evidence": "Пилот решили запустить",
                "owner": None,
                "unexpected": True,
            }
        ],
        "summary": "Лишнее поле",
    }
    errors = validate_structure(invalid)
    assert any("root: unexpected" in error for error in errors)
    assert any("missing fields" in error and "deadline" in error for error in errors)
    assert any("unexpected fields" in error for error in errors)
    assert any("unsupported value" in error for error in errors)


def test_null_is_allowed_but_invented_default_is_not_required():
    assert validate_structure({"facts": [fact(owner=None, deadline=None)]}) == []


def test_evidence_must_be_present_in_source():
    data = {"facts": [fact(evidence="Этой фразы в заметках нет")]}
    assert validate_evidence(data, SOURCE_NOTES) == [
        "facts[0].evidence: not found in source"
    ]
    report = inspect_response(completed(data), SOURCE_NOTES)
    assert report["decision"] == "stop"
    assert report["stage"] == "source"


def test_machine_checks_end_in_review_not_automatic_acceptance():
    report = inspect_response(completed({"facts": [fact()]}), SOURCE_NOTES)
    assert report["decision"] == "review"
    assert report["stage"] == "meaning"


def test_schema_valid_but_false_claim_can_be_rejected_in_semantic_review():
    misleading = fact(
        statement="Пилот запускается для всех пользователей iOS.",
        evidence="для 10% пользователей iOS",
    )
    report = inspect_response(completed({"facts": [misleading]}), SOURCE_NOTES)
    assert report["decision"] == "review"

    final = finish_semantic_review(
        report,
        approved=False,
        reason="Утверждение подменяет 10% пользователей на всех.",
    )
    assert final["decision"] == "stop"
    assert final["stage"] == "meaning"
    assert "10%" in final["review_reason"]


def test_approved_semantic_review_allows_next_step_and_records_reason():
    report = inspect_response(completed({"facts": [fact()]}), SOURCE_NOTES)
    final = finish_semantic_review(
        report,
        approved=True,
        reason="Масштаб и дата подтверждены заметками.",
    )
    assert final["decision"] == "continue"
    assert final["stage"] == "accepted"
    assert final["review_reason"] == "Масштаб и дата подтверждены заметками."


def test_semantic_review_cannot_skip_failed_machine_gate():
    failed = inspect_response(
        {"status": "incomplete", "reason": "max_output_tokens"},
        SOURCE_NOTES,
    )
    with pytest.raises(ValueError, match="decision='review'"):
        finish_semantic_review(failed, approved=True, reason="Принять.")
