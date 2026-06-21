# Урок 7.5 · Evals агентов

**Фаза 7 — Agent Engineering** · **Результат фазы:** Собрать надёжного агента с памятью, планированием, human-in-the-loop и guardrails.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** Агента нельзя улучшать на глаз: нужен тест-сет, метрики и защита от регрессий.

## PROBLEM

Поправил промпт/инструмент агента — на одном примере стало лучше, а на десяти других хуже, и ты этого не видишь. Без **eval-набора** нельзя ни сравнить версии агента, ни поймать регрессию перед выкладкой. Это eval-harness из 2.5, но для агента: оцениваем итог и траекторию (какие инструменты звал, сколько шагов).

## CONCEPT

```
тест-сет {input, expected}
        │ agent_fn (версия агента)
   scorer: success / tool-correctness / шаги
        │ усреднили → success_rate
        ▼
   compare(versии) · has_regression(baseline, candidate)
```

Offline-evals ловят регрессии до прода (как юнит-тесты); online-evals меряют дрейф качества на реальном трафике.

## BUILD IT

Offline eval-harness агента + сравнение версий + детект регрессий: [`code/agent_eval.py`](../code/agent_eval.py).

- `evaluate_agent(agent_fn, cases, scorer)` → `{success_rate, per_case}`;
- `compare_versions(versions, cases)` — рейтинг версий;
- `has_regression(baseline, candidate, cases)` — стало ли хуже.

```bash
python code/agent_eval.py
pytest code -q
```

Тест: рабочий агент → 1.0, сломанный → 0.0, регрессия `good→broken` детектится. Это инструмент выбора версии.

## USE IT

Online-evals и регрессии в проде (мульти-провайдер):

- **LangSmith Evaluation** — offline (на датасетах, как unit-тесты) + online (скоринг прод-трафика); агентные траектории, RAG-метрики; интеграция с pytest/CI.
- **RAGAS** — метрики для RAG/agentic без ручной разметки.
- **Anthropic — empirical evaluations** — как строить надёжные eval-наборы и грейдинг (LLM-as-judge, урок 2.5).
- Включи eval в CI: порог на success_rate, падение — блок мерджа.

## SHIP IT

**Артефакт:** `agent-eval` (skill) → [`outputs/agent-eval/`](../outputs/agent-eval/SKILL.md)

Скилл оценки агента: подкладываешь тест-сет и версии — получаешь рейтинг и флаг регрессии. Зарегистрирован в [`.claude/skills/agent-eval`](../../../.claude/skills/agent-eval/SKILL.md). Связь с 2.5 (eval промптов), 7.4 (поломки), 10.4 (online-трейсинг).

## Материалы

- [LangSmith — Evaluation](https://docs.langchain.com/langsmith/evaluation) — offline/online evals агентов.
- [Ragas — метрики](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/) — метрики для RAG и agentic.
- [Anthropic — Create strong empirical evaluations](https://docs.anthropic.com/en/docs/build-with-claude/develop-tests) — построение eval-наборов.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
