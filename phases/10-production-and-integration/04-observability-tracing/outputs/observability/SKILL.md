---
name: observability
description: "Трейсинг агента курса AI Native: вложенные spans на шаги, длительности, узкое место. Триггеры: «/observability», «трейс агента», «где тормозит агент», «добавь spans», «observability/tracing». Артефакт урока 10.4."
---

# observability — трейсинг шагов агента (spans)

Делает путь агента видимым: вложенные spans (шаг → подшаг) с атрибутами и длительностью — мини-OpenTelemetry для отладки в проде.

## Как пользоваться

1. Оберни шаги агента в spans:

```python
import tracer
tr = tracer.Tracer()
with tr.span("agent_run"):
    with tr.span("retrieve", k=3):
        ...
    with tr.span("llm_call", model="sonnet-4.6"):
        ...
```

2. Смотри дерево: `tr.spans` (name/parent/duration/attrs), `tr.total_duration()`, `tr.slowest()` — узкое место.
3. Для тестов подменяй `clock` на детерминированный.

## Файлы

- `tracer.py` — `Tracer.span(...)`, `total_duration()`, `slowest()`.

## Когда применять

Когда агент выдал странный результат или тормозит — трейс покажет, на каком шаге. В проде переноси на OpenTelemetry GenAI + Phoenix/LangSmith/Langfuse (те же spans, дашборды и evals). Связь: мониторинг (10.2), телеметрия (10.3), evals (7.5).
