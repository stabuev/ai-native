"""Машинная граница ответа модели — Build It урока 2.4.

Модуль не пытается реализовать JSON Schema. Провайдер и его SDK отвечают за
соответствие поддерживаемой части схемы. Здесь видны проверки, которые всё равно
остаются у приложения: статус ответа, синтаксис на границе, точный контракт
конкретного объекта, наличие доказательств в источнике и осознанное решение о смысле.
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


# Это настоящая JSON Schema, передаваемая провайдеру. Все поля объекта fact
# обязательны, а отсутствие owner/deadline выражается null, а не выдуманным значением.
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
    """Собрать единообразный результат gate."""
    return {
        "decision": decision,
        "stage": stage,
        "errors": errors,
        "data": data,
    }


def validate_structure(data: Any) -> list[str]:
    """Проверить точный контракт объекта meeting facts.

    Это намеренно предметная проверка, а не универсальный интерпретатор JSON
    Schema. Возвращает все найденные ошибки; пустой список означает, что форма
    подходит для следующей проверки, но ещё не доказывает истинность значений.
    """
    if not isinstance(data, dict):
        return ["root: expected object"]

    errors: list[str] = []
    root_fields = set(data)
    if root_fields != {"facts"}:
        missing = {"facts"} - root_fields
        extra = root_fields - {"facts"}
        if missing:
            errors.append("root: missing field facts")
        if extra:
            errors.append(f"root: unexpected fields {sorted(extra)}")

    facts = data.get("facts")
    if not isinstance(facts, list):
        errors.append("facts: expected array")
        return errors
    if not facts:
        errors.append("facts: expected at least one item")

    for index, fact in enumerate(facts):
        path = f"facts[{index}]"
        if not isinstance(fact, dict):
            errors.append(f"{path}: expected object")
            continue

        fields = set(fact)
        missing = FACT_FIELDS - fields
        extra = fields - FACT_FIELDS
        if missing:
            errors.append(f"{path}: missing fields {sorted(missing)}")
        if extra:
            errors.append(f"{path}: unexpected fields {sorted(extra)}")

        category = fact.get("category")
        if category not in ALLOWED_CATEGORIES:
            errors.append(f"{path}.category: unsupported value {category!r}")

        for field in ("statement", "evidence"):
            value = fact.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{path}.{field}: expected non-empty string")

        for field in ("owner", "deadline"):
            value = fact.get(field)
            if value is not None and (
                not isinstance(value, str) or not value.strip()
            ):
                errors.append(f"{path}.{field}: expected non-empty string or null")

    return errors


def validate_evidence(data: dict[str, Any], source: str) -> list[str]:
    """Проверить, что каждое evidence дословно присутствует в источнике."""
    errors = []
    for index, fact in enumerate(data["facts"]):
        if fact["evidence"] not in source:
            errors.append(f"facts[{index}].evidence: not found in source")
    return errors


def inspect_response(
    response: dict[str, Any],
    source: str,
) -> dict[str, Any]:
    """Провести машинные gates над нормализованным ответом провайдера.

    ``response`` имеет один из видов:

    - ``{"status": "completed", "output_text": "..."}``;
    - ``{"status": "refusal", "reason": "..."}``;
    - ``{"status": "incomplete", "reason": "..."}``.

    Машинно пригодный результат получает decision=review: к следующему рабочему
    шагу его можно допустить только после отдельной смысловой проверки.
    """
    status = response.get("status")
    if status == "refusal":
        reason = response.get("reason") or "no reason provided"
        return _result("stop", "status", [f"provider refusal: {reason}"])
    if status == "incomplete":
        reason = response.get("reason") or "unknown reason"
        return _result("stop", "status", [f"incomplete response: {reason}"])
    if status != "completed":
        return _result("stop", "status", [f"unsupported status: {status!r}"])

    output_text = response.get("output_text")
    if not isinstance(output_text, str):
        return _result("stop", "syntax", ["output_text: expected string"])

    try:
        data = json.loads(output_text)
    except json.JSONDecodeError as error:
        return _result(
            "stop",
            "syntax",
            [f"invalid JSON at line {error.lineno}, column {error.colno}"],
        )

    errors = validate_structure(data)
    if errors:
        return _result("stop", "structure", errors, data)

    errors = validate_evidence(data, source)
    if errors:
        return _result("stop", "source", errors, data)

    return _result("review", "meaning", [], data)


def finish_semantic_review(
    report: dict[str, Any],
    approved: bool,
    reason: str,
) -> dict[str, Any]:
    """Зафиксировать внешнее смысловое решение после машинных gates.

    ``reason`` обязателен и при принятии, и при отклонении: решение должно
    оставаться объяснимым в трейсе.
    """
    if report.get("decision") != "review":
        raise ValueError("semantic review requires decision='review'")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("semantic review requires a non-empty reason")

    if approved:
        result = _result("continue", "accepted", [], report["data"])
    else:
        result = _result("stop", "meaning", [reason.strip()], report["data"])
    result["review_reason"] = reason.strip()
    return result


def _json_response(data: dict[str, Any]) -> dict[str, str]:
    """Собрать учебный completed-response для локальной демонстрации."""
    return {
        "status": "completed",
        "output_text": json.dumps(data, ensure_ascii=False),
    }


if __name__ == "__main__":
    candidate = {
        "facts": [
            {
                "category": "decision",
                "statement": "Пилот запускается 18 сентября для 10% пользователей iOS.",
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
