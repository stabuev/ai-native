"""Starter for the response boundary gate from lesson 2.4.

Copy this file as ``structured_output.py`` and implement the four marked
functions. The source, instruction, schema, domain constants, result helper,
and demonstration call are already provided.
"""

from __future__ import annotations

import json
from typing import Any


SOURCE_NOTES = """\
Пилот решили запустить 18 сентября для 10% пользователей iOS.
До запуска служба безопасности должна согласовать схему доступа.
Рита отправит схему доступа на согласование до 12 сентября.
Если согласование не получено к 16 сентября, запуск переносится.
Обсудили перевод всех пользователей на новый поток в сентябре,
но решения по этому вопросу не приняли.
Метрики пилота: доля успешных оплат и число обращений в поддержку.
Ответственный за итоговый отчёт пока не назначен.
"""


SYSTEM_INSTRUCTION = """\
Извлекай из заметок только явно сказанные решения, действия, условия,
открытые вопросы и метрики. Не превращай обсуждение в решение.
Для каждого утверждения сохраняй точный подтверждающий фрагмент источника.
Неизвестные owner и deadline возвращай как null: не придумывай значения.
Форма ответа задаётся отдельно переданной JSON Schema.
"""


OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "facts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": [
                            "decision",
                            "action",
                            "condition",
                            "open_question",
                            "metric",
                        ],
                    },
                    "statement": {"type": "string"},
                    "evidence": {"type": "string"},
                    "owner": {
                        "anyOf": [{"type": "string"}, {"type": "null"}]
                    },
                    "deadline": {
                        "anyOf": [{"type": "string"}, {"type": "null"}]
                    },
                },
                "required": [
                    "category",
                    "statement",
                    "evidence",
                    "owner",
                    "deadline",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["facts"],
    "additionalProperties": False,
}


ALLOWED_CATEGORIES = {
    "decision",
    "action",
    "condition",
    "open_question",
    "metric",
}
FACT_FIELDS = {"category", "statement", "evidence", "owner", "deadline"}


def _result(
    decision: str,
    stage: str,
    errors: list[str],
    data: Any = None,
) -> dict[str, Any]:
    """Build one normalized gate report."""
    return {
        "decision": decision,
        "stage": stage,
        "errors": errors,
        "data": data,
    }


def validate_structure(data: Any) -> list[str]:
    """Validate the exact object contract described in the lesson."""
    raise NotImplementedError


def validate_evidence(data: dict[str, Any], source: str) -> list[str]:
    """Report every evidence fragment that is absent from the source."""
    raise NotImplementedError


def inspect_response(
    response: dict[str, Any],
    source: str,
) -> dict[str, Any]:
    """Run status, syntax, structure, and source gates in this order."""
    raise NotImplementedError


def finish_semantic_review(
    report: dict[str, Any],
    approved: bool,
    reason: str,
) -> dict[str, Any]:
    """Record the final human meaning review without bypassing failed gates."""
    raise NotImplementedError


def _json_response(data: dict[str, Any]) -> dict[str, str]:
    """Build a completed response for the local demonstration."""
    return {
        "status": "completed",
        "output_text": json.dumps(data, ensure_ascii=False),
    }


if __name__ == "__main__":
    candidate = {
        "facts": [
            {
                "category": "decision",
                "statement": (
                    "Пилот запускается 18 сентября для 10% пользователей iOS."
                ),
                "evidence": (
                    "Пилот решили запустить 18 сентября "
                    "для 10% пользователей iOS."
                ),
                "owner": None,
                "deadline": "18 сентября",
            }
        ]
    }
    machine_report = inspect_response(_json_response(candidate), SOURCE_NOTES)
    print("После машинных gates:", machine_report["decision"])
    final_report = finish_semantic_review(
        machine_report,
        approved=True,
        reason="Утверждение и масштаб пилота подтверждены источником.",
    )
    print("После смыслового review:", final_report["decision"])
