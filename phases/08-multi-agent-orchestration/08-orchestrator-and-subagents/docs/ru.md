# Урок 8.1 · Оркестратор и субагенты

**Фаза 8 — Мульти-агенты и оркестрация** · **Результат фазы:** Построить мульти-агентный процесс с оркестратором и передачей контекста.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** Координация важнее силы одиночки: оркестратор раздаёт роли, субагенты работают параллельно.

## PROBLEM

Один агент на сложной открытой задаче упирается в контекст и делает всё последовательно. Сильнее — **команда**: оркестратор (lead) декомпозирует задачу и раздаёт части специализированным субагентам, у каждого свой контекст и инструменты. У Anthropic такой подход дал +90% к качеству ресёрча (ценой ~15× токенов).

## CONCEPT

```
        задача
          │ оркестратор (lead): план + декомпозиция
   ┌──────┼──────┐
researcher  writer  reviewer     ← субагенты (свой контекст, свои инструменты)
   └──────┼──────┘
          ▼ оркестратор сводит результаты → ответ
```

Это паттерн **orchestrator-workers**: lead делегирует, субагенты выполняют, lead синтезирует. Каждый субагент изолирован — «шум» его шагов не засоряет общий контекст.

## BUILD IT

Оркестратор, раздающий роли субагентам: [`code/orchestrator.py`](../code/orchestrator.py).

- `Orchestrator.register(role, fn)` — зарегистрировать субагента-роль;
- `delegate(role, task)` — отдать подзадачу субагенту;
- `run(plan)` — выполнить план `[(role, task)]`, собрать результаты по ролям.

```bash
python code/orchestrator.py
pytest code -q
```

Демо: researcher собирает факты → writer пишет черновик по ним → reviewer проверяет. Видно делегирование и сборку; поздние шаги используют результаты ранних.

## USE IT

Agent teams на практике (мульти-провайдер):

- **Claude Code subagents** — изолированные субагенты (`.claude/agents/*.md`), каждый со своим system prompt, контекстом, набором инструментов и моделью (Haiku для дешёвой разведки, Opus для сложного).
- **Claude Agent SDK** — субагенты программно, параллельный запуск.
- Принцип Anthropic: «think like your agents», «scale effort to complexity», «teach the orchestrator how to delegate».

⚠️ Мульти-агент дороже в 4–15× по токенам — применяй там, где это оправдано (Фаза 9).

## SHIP IT

**Артефакт:** Мульти-агентный сценарий → [`outputs/multi-agent-scenario.md`](../outputs/multi-agent-scenario.md)

Сценарий: какие роли субагентов, что делегируем, как сводим. Дальше: как агенты находят друг друга и передают задачи (8.2), как делят общий контекст (8.3).

## Материалы

- [Anthropic — How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — orchestrator-worker на практике.
- [Anthropic — Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — паттерн orchestrator-workers.
- [Claude Code — Subagents](https://code.claude.com/docs/en/sub-agents) — изолированные субагенты с ролями.

---
**Часы:** ~5 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
