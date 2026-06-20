# Урок 2.4 · Системные промпты и структурированный вывод

**Фаза 2 — Промпт-инжиниринг** · **Результат фазы:** Писать воспроизводимые промпты и измерять их качество через eval-harness.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** Если ответ парсит программа — он должен быть схемой, а не прозой.

## PROBLEM

Когда вывод модели идёт в код (БД, API, UI), свободный текст — катастрофа: то лишние пояснения, то поле пропало, то число пришло строкой. «Верни JSON» в промпте не гарантирует валидную структуру. Нужны **системный промпт**, задающий формат, и **валидатор**, который проверяет соответствие схеме на нашей стороне.

## CONCEPT

```
system prompt (роль + строгий формат)
        │
        ▼
ответ модели ──extract_json──► объект ──validate_schema──► ✓ / список ошибок
   (часто в ```json … ```)        (типы, обязательные поля)
```

Два уровня надёжности: **(1)** провайдерский structured output / function calling заставляет модель держать схему; **(2)** свой валидатор — страховка, что пришедшее реально ей соответствует (доверяй, но проверяй).

## BUILD IT

Извлечение JSON + валидатор мини-схемы: [`code/structured_output.py`](../code/structured_output.py).

- `extract_json(text)` — снять ```json-ограждение и распарсить;
- `validate_schema(obj, schema)` — проверить типы и обязательные поля (boolean не считается integer);
- `SYSTEM_PROMPT` + `SCHEMA` — пример под извлечение тикета.

```bash
python code/structured_output.py
pytest code -q
```

Валидатор ловит то, что молча ломает прод: пропущенное обязательное поле, `priority: true` вместо числа, не-JSON в ответе.

## USE IT

Проси у провайдера гарантированную структуру (мульти-провайдер):

```python
schema = {"type": "object", "properties": {
    "title": {"type": "string"}, "priority": {"type": "integer"}},
    "required": ["title", "priority"], "additionalProperties": False}

# OpenAI — Structured Outputs (response_format / text.format = json_schema)
OpenAI().responses.create(model="gpt-5.x", input="...",
    text={"format": {"type": "json_schema", "name": "ticket", "schema": schema}})
# Google — responseSchema в config
genai.Client().models.generate_content(model="gemini-2.x-flash", contents="...",
    config={"response_mime_type": "application/json", "response_schema": schema})
# Anthropic — через tool use (function calling): описываешь input_schema инструмента
```

Даже с гарантией провайдера прогоняй ответ через свой `validate_schema` — это дешёвая страховка.

## SHIP IT

**Артефакт:** Системный промпт + JSON-схема → [`outputs/system-prompt-and-schema.md`](../outputs/system-prompt-and-schema.md)

Готовая пара «system prompt + схема + валидатор» под извлечение структуры из текста. Возвращается в Фазе 5 (NL→SQL, отчёты) и Фазе 6 (инструменты MCP).

## Материалы

- [OpenAI — Structured model outputs](https://platform.openai.com/docs/guides/structured-outputs) — гарантированное соответствие JSON-схеме.
- [OpenAI — Introducing Structured Outputs](https://openai.com/index/introducing-structured-outputs-in-the-api/) — зачем и чем отличается от JSON mode.
- [JSON Schema](https://json-schema.org/) — стандарт описания схем (типы, required, additionalProperties).

---
**Часы:** ~3 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
