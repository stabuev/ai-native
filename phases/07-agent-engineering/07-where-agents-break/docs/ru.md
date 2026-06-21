# Урок 7.4 · Где агенты ломаются

**Фаза 7 — Agent Engineering** · **Результат фазы:** Собрать надёжного агента с памятью, планированием, human-in-the-loop и guardrails.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** Агенты ломаются предсказуемо — петли, дрейф цели, бесконечная работа; это ловится инженерно.

## PROBLEM

Автономный агент рано или поздно зависает: крутится в петле (повторяет одно действие), дрейфует от цели (увлёкся не тем) или просто не останавливается. Если не ловить эти режимы, агент жжёт токены и время впустую. Воспроизведём поломки и встроим детекторы.

## CONCEPT

```
типовые поломки:               детектор:
- петля (повтор действия)   →  detect_loop (N одинаковых подряд)
- дрейф цели                →  goal_relatedness < порога
- бесконечная работа        →  лимит шагов
```

Это «предохранители» вокруг agent loop из 7.1. Глубже — self-reflection (Reflexion): агент анализирует неудачу и корректирует подход, а не повторяет её.

## BUILD IT

Воспроизведение петель/дрейфа + детекторы: [`code/agent_failures.py`](../code/agent_failures.py).

- `detect_loop(actions, repeat)` — N одинаковых действий подряд;
- `goal_relatedness(goal, action)` — связь действия с целью (грубая оценка дрейфа);
- `run_guarded(policy, goal, max_steps, repeat, drift_threshold)` — гоняет policy и возвращает статус: `done` / `loop_detected` / `goal_drift` / `step_limit`.

```bash
python code/agent_failures.py
pytest code -q
```

Демо: зацикленная policy → `loop_detected`; нормальная → `done`; бесконечная без повторов → `step_limit`. Поломки ловятся **до** того, как агент сожжёт бюджет.

## USE IT

Инженерные приёмы контроля (мульти-провайдер):

- **Лимит шагов/времени/бюджета** — жёсткий потолок на цикл (как в agent loop 7.1).
- **Детекция повторов** — одинаковые tool_call подряд → стоп или смена стратегии.
- **Привязка к цели** — периодически сверять действия с исходной целью (анти-дрейф).
- **Self-reflection (Reflexion)** — после неудачи попросить агента отрефлексировать и перепланировать.
- **Наблюдаемость** — логировать трейс (Фаза 10), чтобы видеть, где сломалось.

## SHIP IT

**Артефакт:** prompt-debug-agent → [`outputs/prompt-debug-agent/`](../outputs/prompt-debug-agent/README.md)

Набор детекторов (петля/дрейф/лимит) + плейбук отладки агента: симптом → причина → приём. Завершает Фазу 7: агент с памятью, планом, guardrails и предохранителями от поломок.

## Материалы

- [Anthropic — Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — когда агент уместен, ограничения автономии.
- [Shinn et al., 2023 — Reflexion](https://arxiv.org/abs/2303.11366) — self-reflection и обучение на неудачах без дообучения.
- [Anthropic — Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — context rot и длинные горизонты.

---
**Часы:** ~5 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
