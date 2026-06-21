# Урок 10.4 · Observability и трейсинг агентов

**Фаза 10 — Production и интеграция** · **Результат фазы:** Встроить ИИ в рабочий инструмент с мониторингом токенов и стоимости.
<!-- **Requires:** observability-бэкенд — только для блока USE IT -->

> **MOTTO.** Агент недетерминирован — без трейса шагов отладка в проде превращается в гадание.

## PROBLEM

Мониторинг (10.2) даёт агрегаты «здорово/нет», но когда агент выдал странный результат, нужно увидеть **весь путь**: какие шаги, какие инструменты, какой retrieval, где время и токены. Это **трейсинг**: вложенные spans на каждый шаг агента — как в OpenTelemetry GenAI.

## CONCEPT

```
trace (один запрос)
 └─ span: agent_run
     ├─ span: retrieve (k=3)        ← attrs, длительность
     ├─ span: llm_call (model, токены)
     └─ span: tool (args, результат)
   → дерево spans: где узкое место, где упало, сколько стоило
```

Spans вложены (шаг → подшаг), несут атрибуты (модель, токены) и длительность. Из трейса видно bottleneck и точку отказа.

## BUILD IT

Трейсер шагов агента (вложенные spans) с нуля: [`code/tracer.py`](../code/tracer.py).

- `Tracer.span(name, **attrs)` — контекст-менеджер: вложенность, родитель, длительность;
- `total_duration()`, `slowest()` — сводка и узкое место (clock подменяем для тестов).

```bash
python code/tracer.py
pytest code -q
```

Тест с фейковым clock: вложенные spans с правильным родителем и длительностью, `slowest` находит узкое место. Это мини-OpenTelemetry для агента.

## USE IT

Готовые платформы трейсинга/observability (мульти-инструмент):

- **Arize Phoenix** — open-source, на OpenTelemetry/OpenInference; трейсинг + evals локально, без отправки в SaaS; поддержка OpenAI/Claude Agent SDK, LangGraph, CrewAI.
- **LangSmith** — трейсинг + evals (offline/online), framework-agnostic, CI-интеграция.
- **Langfuse** — open-source трейсинг, токены/стоимость, LLM-as-judge.
- Все на стандарте **OpenTelemetry GenAI** (`gen_ai.*`) — единый формат spans без вендор-лока.

## SHIP IT

**Артефакт:** `observability` (skill) → [`outputs/observability/`](../outputs/observability/SKILL.md)

Скилл трейсинга: оборачиваешь шаги агента в spans, получаешь дерево с длительностями и узким местом. Зарегистрирован в [`.claude/skills/observability`](../../../.claude/skills/observability/SKILL.md). Связь с 10.2 (мониторинг), 10.3 (телеметрия), 7.5 (online-evals), 7.4 (отладка поломок).

## Материалы

- [Arize Phoenix](https://arize.com/docs/phoenix) — open-source трейсинг/eval на OpenTelemetry.
- [LangSmith](https://docs.langchain.com/langsmith/) — трейсинг и оценка агентов.
- [OpenTelemetry — GenAI observability](https://opentelemetry.io/blog/2026/genai-observability/) — стандартные spans/метрики.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
