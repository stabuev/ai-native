# Урок 8.2 · A2A и MCP Server Cards

**Фаза 8 — Мульти-агенты и оркестрация** · **Результат фазы:** Построить мульти-агентный процесс с оркестратором и передачей контекста.
<!-- **Requires:** A2A-совместимый агент/SDK — только для блока USE IT -->

> **MOTTO.** Чтобы агенты сотрудничали, им нужен общий язык: карточки возможностей + конверт задачи.

## PROBLEM

В 8.1 субагенты были «вшиты» в оркестратор. Но агенты от разных команд/фреймворков должны находить друг друга и передавать задачи без ручной интеграции. Для этого есть **A2A** (agent-to-agent): агент публикует **карточку** (что умеет), другой агент её находит и шлёт **задачу** в стандартном конверте.

## CONCEPT

```
Agent Card (JSON): {name, skills, endpoint, auth}   ← discovery
        │ find_agent: подобрать по навыкам
        ▼
Task (id, message) ──► agent ──► Artifact (результат)   ← A2A-конверт
```

A2A дополняет MCP: **MCP** соединяет агента с инструментами, **A2A** — агента с агентом. Оба используют JSON-RPC/HTTP и discovery через карточки.

## BUILD IT

Карточки агентов + передача задач: [`code/a2a.py`](../code/a2a.py).

- `AgentCard(name, skills, handler)` — карточка возможностей;
- `find_agent(task, cards)` — discovery: подобрать агента по навыкам;
- `send_task(task, card)` / `route_and_run(task, cards)` — A2A-конверт результата.

```bash
python code/a2a.py
pytest code -q
```

Демо: «sql запрос» → sql-agent, «поиск по документам» → doc-agent, «нарисуй картинку» → нет агента. Это discovery + handoff в миниатюре.

## USE IT

Автообнаружение инструментов и агентов (мульти-платформа):

- **A2A Protocol** (Google → Linux Foundation) — Agent Card по well-known URL, Task/Message/Artifact, стриминг (SSE), enterprise-auth; 50+ партнёров.
- **MCP discovery** — `tools/list` и server cards: клиент сам узнаёт, что умеет сервер (урок 6.3).
- Комбинация: MCP даёт агенту инструменты, A2A — оркеструет агентов между собой.

## SHIP IT

**Артефакт:** Схема A2A-взаимодействия → [`outputs/a2a-schema.md`](../outputs/a2a-schema.md)

Схема: карточки агентов твоего процесса, какие навыки, как находят друг друга, формат задачи. Дальше: общий контекст и конфликты (8.3).

## Материалы

- [A2A Protocol](https://a2a-protocol.org/latest/) — стандарт agent-to-agent (карточки, Task/Artifact).
- [a2aproject/A2A](https://github.com/a2aproject/A2A) — спецификация и реализации.
- [MCP — Specification](https://modelcontextprotocol.io/specification/2025-11-25) — discovery и server cards.

---
**Часы:** ~5 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
