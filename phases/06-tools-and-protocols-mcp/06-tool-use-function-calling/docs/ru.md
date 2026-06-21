# Урок 6.1 · Tool use / function calling изнутри

**Фаза 6 — Инструменты и протоколы (MCP)** · **Результат фазы:** Объяснить tool use изнутри и поднять собственный MCP-сервер с контролем доступа.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** Модель не вызывает функции сама — она просит вызвать; протокол — это схемы, tool_call и tool_result.

## PROBLEM

«Модель сходила в базу и посчитала» — звучит как магия, но модель не исполняет код. Она лишь возвращает **tool_call** (имя инструмента + аргументы по JSON-схеме), а исполняет **твой** код, и результат (**tool_result**) уходит обратно в модель. Не понимая этот протокол, нельзя ни отладить tool use, ни безопасно подключить инструменты.

## CONCEPT

```
схемы инструментов → модель → tool_call(name, args)
                                   │ твой диспетчер: валидирует по схеме, исполняет
                                   ▼
                              tool_result ──► модель ──► финал
```

Три кита: **схема** (что за инструмент и аргументы), **tool_call** (запрос модели), **tool_result** (ответ твоего кода). Это фундамент, на котором стоит MCP (6.2+).

## BUILD IT

Цикл function-calling с нуля: [`code/function_calling.py`](../code/function_calling.py).

- `Tool(name, description, schema, fn)` — инструмент с JSON-схемой;
- `validate_args(args, schema)` — проверка аргументов по схеме;
- `dispatch(tool_call, registry)` — валидировать и исполнить;
- `run(model_fn, registry)` — цикл tool_call → tool_result → final.

```bash
python code/function_calling.py
pytest code -q
```

Модель здесь — детерминированный stub (офлайн); меняешь его на LLM — протокол тот же. Видно, что «агентность» начинается с этого цикла.

## USE IT

Тот же протокол — через API провайдера (мульти-провайдер):

```python
tools = [{"name": "add", "description": "сложить",
          "input_schema": {"type": "object", "properties": {"a": {"type": "number"},
          "b": {"type": "number"}}, "required": ["a", "b"]}}]
# Anthropic: messages.create(..., tools=tools) → блок tool_use → выполнить → tool_result
# OpenAI:    responses.create(..., tools=[{"type":"function", ...}]) → tool call → role:"tool"
# Google:    function_declarations в config → functionCall → functionResponse
```

Форма различается синтаксисом, но цикл один: схема → запрос модели → твой код → результат назад.

## SHIP IT

**Артефакт:** Описание набора инструментов (схемы) → [`outputs/tool-schemas.md`](../outputs/tool-schemas.md)

Готовые JSON-схемы для типового тулсета (read/search/calc) + правила описания (имя, описание-триггер, строгие типы). Дальше: стандартизуем доступ к инструментам через MCP (6.2).

## Материалы

- [Anthropic — Tool use](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview) — tool use в Claude изнутри.
- [OpenAI — Function calling](https://platform.openai.com/docs/guides/function-calling) — схемы и цикл tool calling.
- [JSON Schema](https://json-schema.org/) — как описывать параметры инструментов.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
