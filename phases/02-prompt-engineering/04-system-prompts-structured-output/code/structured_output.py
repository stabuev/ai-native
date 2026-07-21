"""Структурированный вывод: JSON-схема + валидатор — Build It для урока 2.4.

Без зависимостей. Системный промпт задаёт формат, а валидатор гарантирует, что
ответ модели реально соответствует схеме (типы, обязательные поля). Плюс
извлечение JSON из текста — модель часто оборачивает его в ```json … ```.
"""
import json

# Сопоставление типов мини-схемы с типами Python.
_TYPES = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def extract_json(text):
    """Достать JSON из ответа: снять ```json-ограждение и распарсить."""
    t = text.strip()
    if t.startswith("```"):
        t = t[3:]
        if t.lower().startswith("json"):
            t = t[4:]
        t = t.rsplit("```", 1)[0]
    return json.loads(t)


def validate_schema(obj, schema):
    """Проверить объект по мини-схеме {field: {type, required}}. → список ошибок."""
    errors = []
    if not isinstance(obj, dict):
        return ["корень: ожидался объект (dict)"]
    for field, spec in schema.items():
        if field not in obj:
            if spec.get("required", False):
                errors.append(f"{field}: отсутствует обязательное поле")
            continue
        val = obj[field]
        # boolean — подкласс int в Python, отделяем явно
        if spec["type"] in ("number", "integer") and isinstance(val, bool):
            errors.append(f"{field}: ожидался {spec['type']}, получен boolean")
        elif not isinstance(val, _TYPES[spec["type"]]):
            errors.append(f"{field}: ожидался {spec['type']}")
    return errors


# Пример системного промпта + схемы под извлечение тикета.
SYSTEM_PROMPT = (
    "Ты парсер обращений. Верни СТРОГО JSON по схеме, без пояснений: "
    '{"title": string, "priority": integer (1..5), "urgent": boolean}.'
)
SCHEMA = {
    "title": {"type": "string", "required": True},
    "priority": {"type": "integer", "required": True},
    "urgent": {"type": "boolean", "required": False},
}


if __name__ == "__main__":
    raw = '```json\n{"title": "Не грузит отчёт", "priority": 2, "urgent": true}\n```'
    obj = extract_json(raw)
    print("Распарсено:", obj)
    print("Ошибки схемы:", validate_schema(obj, SCHEMA) or "нет")
    bad = {"title": "X", "priority": True}        # priority — boolean вместо integer
    print("Плохой объект:", validate_schema(bad, SCHEMA))
