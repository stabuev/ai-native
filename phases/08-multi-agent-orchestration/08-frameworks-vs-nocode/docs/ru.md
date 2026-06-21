# Урок 8.4 · Оркестрация: фреймворки vs no-code

**Фаза 8 — Мульти-агенты и оркестрация** · **Результат фазы:** Построить мульти-агентный процесс с оркестратором и передачей контекста.
<!-- **Requires:** аккаунт/инстанс инструмента — только для блока USE IT -->

> **MOTTO.** Под капотом фреймворков и no-code — один и тот же граф: узлы, рёбра, состояние.

## PROBLEM

Свой оркестратор (8.1) понятен, но в проде выбирают между **код-фреймворками** (LangGraph, CrewAI, AutoGen), **gateway-платформами** (OpenClaw/Hermes, урок 4.5) и **no-code/workflow** (n8n). Легко взять не тот класс инструмента. Чтобы выбирать осознанно, нужно понять, что у всех внутри — граф процесса — и где каждый класс уместен.

## CONCEPT

```
граф процесса = узлы (шаги) + рёбра (переходы, в т.ч. условные/циклы) + state
   └─ это и есть «движок» LangGraph, n8n-флоу, своего оркестратора

выбор класса инструмента:
  from-scratch / SDK   контроль, нет лок-ина, надо писать всё
  код-фреймворк        LangGraph (граф/циклы), CrewAI (роли), AutoGen (диалоги)
  no-code / workflow    n8n (визуально, 400+ интеграций, AI-agent-ноды)
  gateway-платформа     OpenClaw / Hermes (персональный агент, каналы) — 4.5
```

## BUILD IT

Мини-граф процесса (как LangGraph) своими руками: [`code/mini_graph.py`](../code/mini_graph.py).

- `Graph.add_node/add_edge/add_conditional/run` — узлы, рёбра, условные ветвления и циклы поверх общего `state`;
- лимит шагов как guard от бесконечных циклов (7.4).

```bash
python code/mini_graph.py
pytest code -q
```

Тест: линейный граф, условное ветвление, цикл с выходом по условию. Это ядро любого оркестратора — у LangGraph то же, плюс персистентность и инструменты.

## USE IT

Тот же процесс — в готовых инструментах (мульти-инструмент):

- **LangGraph** — стейтовый граф с циклами, persistence, human-in-the-loop; «низкоуровневый» контроль (Uber, Klarna, J.P. Morgan).
- **CrewAI** — оркестрация по ролям (researcher/analyst/writer), быстрый старт, но более «opinionated».
- **n8n** — визуальный workflow с AI-Agent-нодами (на базе LangChain), 400+ интеграций, MCP, human-in-the-loop; смешивает детерминированные шаги и ИИ.
- Правило: **детерминированная автоматизация с парой ИИ-шагов → n8n**; **сложная агентная логика с циклами/состоянием → LangGraph/код**; **роли-команда → CrewAI**; **персональный агент с каналами → OpenClaw/Hermes**.

## SHIP IT

**Артефакт:** Матрица «когда фреймворк, когда no-code» → [`outputs/orchestration-matrix.md`](../outputs/orchestration-matrix.md)

Карта выбора (from-scratch ↔ SDK ↔ LangGraph/CrewAI/AutoGen ↔ OpenClaw/Hermes ↔ n8n): критерии, плюсы/минусы, когда что. Связь с 8.1 (оркестратор), 4.5 (платформы), 7.4 (лимиты/циклы).

## Материалы

- [LangGraph — overview](https://docs.langchain.com/oss/python/langgraph/overview) — стейтовый граф агентов.
- [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) — оркестрация по ролям.
- [n8n — Advanced AI](https://docs.n8n.io/advanced-ai/) — no-code workflow с AI-агентами.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
