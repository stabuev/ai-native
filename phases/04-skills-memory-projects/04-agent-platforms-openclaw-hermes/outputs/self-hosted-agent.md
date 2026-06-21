# Артефакт: свой агент на self-hosted платформе

Как упаковать свой навык и запустить персонального агента у себя. Мини-рантайм — [`code/skill_runtime.py`](../code/skill_runtime.py).

## Шаги

1. **Скилл** — оформи навык как `SKILL.md` (урок 4.1) или по стандарту agentskills.io (переносим между платформами).
2. **Платформа** — поставь self-hosted рантайм:
   - **OpenClaw** — `npm install -g openclaw@latest && openclaw onboard` (гейтвей + каналы).
   - **Hermes** — `curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash` (self-improving loop; умеет импортировать конфиг из OpenClaw).
3. **Модель** — подключи любую (OpenAI-совместимый API или локальная через Ollama) — model-agnostic.
4. **Память + MCP** — включи память между сессиями (4.2) и инструменты через MCP (Ф6).
5. **Каналы** — Telegram/Slack/Signal/… для доступа отовсюду.

## Как это работает (мини-версия)

```python
from skill_runtime import Runtime
rt = Runtime()
rt.load(MY_SKILL_MD, handler=my_fn)   # реестр скиллов
rt.handle("сообщение пользователя")   # роут → скилл → память
```

## Выбор платформы

| | OpenClaw | Hermes |
|---|---|---|
| Сильная сторона | каналы, экосистема, ClawHub | self-improving loop, безопасность |
| Модели | любой OpenAI-совместимый (вкл. Ollama) | любые, лучше Hermes-серия |
| Лицензия | MIT, self-host | MIT, self-host |

## Правила безопасности

- Self-host решает приватность/суверенитет данных (урок 11.1), но это **исполнение кода у тебя**.
- Обязательны **sandbox**, least-privilege инструментов и защита от **prompt injection** (урок 11.5).
- Человек на критичных/необратимых действиях (урок 7.3).
