# Урок 7.1 · Цикл reason → act → observe

**Фаза 7 — Agent Engineering** · **Результат фазы:** Собрать надёжного агента с памятью, планированием, human-in-the-loop и guardrails.

> **MOTTO.** Агент — это не модель, а цикл: подумал → сделал → посмотрел на результат → повторил.

## PROBLEM

«Агент» звучит как магия, пока не видишь цикл изнутри. Без этого нельзя ни отладить зависание, ни понять, почему агент крутится в петле или зовёт несуществующий инструмент. А ещё кажется, что для агента обязательно нужен дорогой LLM и API-ключ — на самом деле сам механизм от модели не зависит.

## CONCEPT

Любой агент — это петля из трёх шагов вокруг **policy** (того, кто принимает решение) и набора **инструментов** (того, что делает руками):

```
        ┌──────────────────────────────────────┐
        │                                       │
   goal ▼            (reason)                    │
        policy ── Action(tool, args) ──► tool ──┘
        ▲                                  │
        │            (observe)             │ (act)
        └────────── observation ◄──────────┘
                         │
              Action(final) ──► ответ
```

Policy на каждом витке смотрит на цель и историю и выбирает: вызвать инструмент или дать финальный ответ. Результат инструмента (`observation`) возвращается в историю — и это **память** агента в простейшем виде. Петля повторяется до финала или до лимита шагов.

## BUILD IT

Цикл реализован с нуля, без зависимостей: [`code/agent_loop.py`](../code/agent_loop.py).

- `run_agent(goal, tools, policy, max_steps)` — сам цикл reason→act→observe;
- `Action` — единая форма решения (`tool` или `final`);
- `RuleBasedPolicy` — детерминированная «модель» (чтобы урок шёл офлайн);
- **guardrails** уже встроены: лимит шагов (петля → `AgentError`) и проверка неизвестного инструмента.

Запуск демо и тестов:

```bash
python code/agent_loop.py
pytest code -q
```

Демо решает `(2 + 3) * 4 - 1` за три вызова инструментов — видно, как результат каждого шага становится входом следующего.

## USE IT

То же самое — с настоящей моделью. Меняется **только policy**: вместо правил её роль играет LLM через function calling, а форма `Action` остаётся прежней. <!-- **Requires:** платный API-ключ провайдера -->

```python
# набросок LLM-policy под тот же run_agent(...)
def llm_policy(goal, history):
    resp = client.messages.create(
        model="claude-haiku-4-5",          # дешёвая модель на роль «рассуждателя»
        tools=TOOL_SCHEMAS,                 # схемы add/sub/mul
        messages=build_messages(goal, history),
    )
    block = resp.content[0]
    if block.type == "tool_use":
        return Action("tool", block.name, tuple(block.input.values()))
    return Action("final", answer=block.text)
```

Вывод урока: «агентность» — это инженерия цикла и инструментов, а не сама модель. Модель — заменяемая деталь (мост к Фазе 9: на роль policy берут модель подешевле).

## SHIP IT

**Артефакт:** `agent-loop` (skill) → [`outputs/skill-agent-loop.md`](../outputs/skill-agent-loop.md)

Переиспользуемый каркас цикла с guardrails: подставляешь свои инструменты и policy. Дальше в фазе наращивается память и планирование (7.2), human-in-the-loop (7.3), разбор поломок (7.4).

## Материалы

- [ReAct: Reasoning + Acting (arXiv 2210.03629)](https://arxiv.org/abs/2210.03629) — первоисточник цикла reason→act→observe.
- [Anthropic — Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — агент как LLM с инструментами в цикле; когда он вообще нужен.
- [Anthropic — Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) — как проектировать инструменты и интерфейс агент↔среда.

---
**Часы:** ~5 · **DoD:** `pytest code -q` зелёный (5 тестов), демо запускается, ru.md заполнен. ✅ **Урок готов** (эталон уровня «агенты»).
