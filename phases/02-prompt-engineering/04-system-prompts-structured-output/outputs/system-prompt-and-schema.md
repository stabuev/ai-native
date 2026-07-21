# Артефакт: системный промпт + JSON-схема

Пара «системный промпт + схема + валидатор» для надёжного структурированного вывода. Код — в [`code/structured_output.py`](../code/structured_output.py).

## Системный промпт (пример)

```
Ты парсер обращений в поддержку. Верни СТРОГО JSON по схеме, без пояснений и без markdown:
{"title": string, "priority": integer (1..5), "urgent": boolean}
Если данных не хватает — ставь priority=3, urgent=false.
```

## JSON-схема

```json
{
  "type": "object",
  "properties": {
    "title":    {"type": "string"},
    "priority": {"type": "integer"},
    "urgent":   {"type": "boolean"}
  },
  "required": ["title", "priority"],
  "additionalProperties": false
}
```

## Валидатор (наша сторона)

```python
from structured_output import extract_json, validate_schema, SCHEMA
obj = extract_json(model_response)          # снимет ```json-ограждение
errors = validate_schema(obj, SCHEMA)       # [] = всё в порядке
assert not errors, errors
```

## Правила

- **Двойная защита:** проси structured output у провайдера И проверяй своим валидатором.
- `additionalProperties: false` + все нужные поля в `required` — меньше «лишнего» и пропусков.
- **boolean ≠ integer** — частая ловушка; валидатор её ловит.
- Порядок полей в ответе следует порядку в схеме.
- Где задаётся: OpenAI — `text.format=json_schema`; Google — `response_schema`; Anthropic — через tool use (`input_schema`).
