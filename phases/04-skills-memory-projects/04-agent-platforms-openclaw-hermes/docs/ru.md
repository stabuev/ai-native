# Урок 4.5 · Агентные платформы: OpenClaw / Hermes

**Фаза 4 — Скиллы, память и проекты (слой персистентности)** · **Результат фазы:** Упаковывать способности в SKILL.md, хранить контекст в памяти и собирать рабочие проекты.
<!-- **Requires:** self-hosted платформа (OpenClaw/Hermes) + API-ключ — только для блока USE IT -->

> **MOTTO.** Скилл + память + мульти-модель = персональный агент, который живёт у тебя и доступен везде.

## PROBLEM

Скиллы (4.1) и память (4.2) по отдельности — это детали. В 2026 появились **self-hosted агентные платформы**, которые собирают их в постоянного персонального агента: грузят скиллы, помнят контекст между сессиями, ходят в несколько моделей и отвечают в твоих мессенджерах. Поймём механику, собрав мини-рантайм, и сравним готовые платформы.

## CONCEPT

```
self-hosted агент-рантайм (OpenClaw / Hermes)
   ├─ skills (SKILL.md / agentskills.io)   ← способности (4.1)
   ├─ memory (между сессиями)               ← контекст (4.2)
   ├─ model router (любая модель)           ← мульти-модель (Ф9)
   ├─ MCP / tools                           ← инструменты (Ф6)
   └─ channels (Telegram/Slack/…)           ← доступ отовсюду
```

Ключевая идея: агент **у тебя** (данные не уходят наружу — мост к 11.1), а скиллы переносимы между платформами (стандарт agentskills.io).

## BUILD IT

Загрузка скилла в локальный рантайм + роутинг + память: [`code/skill_runtime.py`](../code/skill_runtime.py).

- `parse_skill` — разбор SKILL.md (как в 4.1);
- `Runtime.load/route/handle` — грузим скиллы, роутим сообщение в подходящий, держим память.

```bash
python code/skill_runtime.py
pytest code -q
```

Это уменьшенная копия того, что делают OpenClaw/Hermes: реестр скиллов + маршрутизация + память между сообщениями.

## USE IT

Готовые платформы (self-hosted, MIT, model-agnostic):

- **OpenClaw** — гейтвей-оркестратор, messaging-first (Telegram/Slack/Signal/…), ClawHub-маркетплейс скиллов, любой OpenAI-совместимый бэкенд (вкл. локальные через Ollama).
- **Hermes Agent** (Nous Research) — self-improving loop: после задачи пишет переиспользуемый скилл и улучшает его; 7-слойная модель безопасности; автоимпорт конфигурации из OpenClaw.
- Оба ставятся за ~$5/мес + стоимость модели; скиллы переносимы (agentskills.io).

⚠️ Self-host решает приватность/суверенитет (11.1), но это исполнение кода у тебя — нужен sandbox и защита от prompt injection (11.5).

## SHIP IT

**Артефакт:** Свой агент на self-hosted платформе → [`outputs/self-hosted-agent.md`](../outputs/self-hosted-agent.md)

Гайд: упаковать свой скилл (4.1) → положить в рантайм → подключить модель и канал. Связь со скиллами (4.1), памятью (4.2), MCP (Ф6), FinOps (Ф9), безопасностью (11.5).

## Материалы

- [openclaw/openclaw](https://github.com/openclaw/openclaw) — self-hosted агент-гейтвей (MIT).
- [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) — агент с self-improving loop (MIT).
- [Claude — Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) — формат скиллов, переносимых между платформами.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
