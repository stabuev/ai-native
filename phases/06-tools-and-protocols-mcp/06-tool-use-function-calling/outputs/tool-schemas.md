# Артефакт: описание набора инструментов (схемы)

Готовые JSON-схемы для типового тулсета + правила их описания. Цикл вызова — [`code/function_calling.py`](../code/function_calling.py).

## Схемы инструментов

```json
[
  {
    "name": "search_docs",
    "description": "Найти релевантные документы в базе знаний по запросу",
    "input_schema": {
      "type": "object",
      "properties": {
        "query": {"type": "string", "description": "поисковый запрос"},
        "k": {"type": "integer", "description": "сколько вернуть", "default": 3}
      },
      "required": ["query"]
    }
  },
  {
    "name": "get_metric",
    "description": "Получить значение бизнес-метрики за период",
    "input_schema": {
      "type": "object",
      "properties": {
        "metric": {"type": "string", "enum": ["revenue", "orders", "avg_check"]},
        "period": {"type": "string", "description": "напр. 2026-Q2"}
      },
      "required": ["metric", "period"]
    }
  }
]
```

## Правила описания инструментов

- **name** — короткий, глагол+объект (`search_docs`, не `tool1`).
- **description** — что делает И когда применять (это «триггер» выбора, как у скиллов 4.1).
- **строгие типы** — `enum` для фиксированных значений, `required` для обязательных.
- **минимум инструментов в контексте** — 3–5 ключевых всегда, остальное по запросу (context engineering, урок 4.4).
- **идемпотентность и безопасность** — отдельный флаг для write-инструментов (урок 6.5).

## Где задаётся у провайдеров

- Anthropic: `tools=[{name, description, input_schema}]`
- OpenAI: `tools=[{"type":"function","function":{name, description, parameters}}]`
- Google: `function_declarations`
- MCP: `tools/list` отдаёт `inputSchema` (урок 6.3) — один набор для всех клиентов.
