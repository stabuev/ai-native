# Артефакт: схема A2A-взаимодействия

Как агенты находят друг друга и передают задачи. Код — [`code/a2a.py`](../code/a2a.py).

## Agent Card (карточка возможностей)

```json
{
  "name": "sql-agent",
  "description": "Отвечает на вопросы к БД через NL→SQL",
  "skills": ["sql", "база", "запрос", "метрика"],
  "endpoint": "https://.../a2a",
  "auth": "oauth2"
}
```

## Поток A2A

```
1. discovery   client читает Agent Card (well-known URL) → знает навыки и endpoint
2. task        client → {task_id, message} выбранному агенту
3. work        агент выполняет (может стримить статус через SSE)
4. artifact    агент → результат (текст/файл/структура) в конверте
```

## Конверт задачи/результата

```python
from a2a import AgentCard, route_and_run
cards = [AgentCard("sql-agent", ["sql","запрос"], handler), ...]
env = route_and_run("сделай sql запрос по продажам", cards)
# env: {status, agent, task, result}
```

## A2A vs MCP

| | MCP | A2A |
|---|---|---|
| Соединяет | агент ↔ инструменты/данные | агент ↔ агент |
| Discovery | `tools/list`, server card | Agent Card (well-known URL) |
| Транспорт | JSON-RPC (STDIO/HTTP) | JSON-RPC/HTTP + SSE |

## Правила

- **Карточка — честная**: навыки и ограничения, по ним идёт discovery.
- **Стандартный конверт** (Task/Message/Artifact) — не самописные форматы.
- **Auth и аудит** на границе агентов (урок 6.5): не доверяй чужому агенту слепо.
- MCP + A2A вместе: инструменты каждому агенту (MCP) + оркестрация агентов (A2A).
