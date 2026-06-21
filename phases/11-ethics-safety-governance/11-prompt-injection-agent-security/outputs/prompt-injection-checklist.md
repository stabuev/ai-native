# Артефакт: чек-лист защиты от prompt injection

Эшелонированная защита агента (по OWASP LLM01). Код-демо — [`code/injection_defense.py`](../code/injection_defense.py).

## Модель угрозы

- **Direct injection (jailbreak)** — пользователь пытается переписать системный промпт.
- **Indirect injection / RAG-poisoning** — скрытая инструкция в данных (веб, письмо, чанк RAG).
- **Excessive agency** — injection → агент вызывает опасный инструмент.

## Чек-лист (defense-in-depth, ни один слой не достаточен)

**Данные vs инструкции**
- [ ] Недоверенные данные помечены как данные; не выполнять инструкции из них.
- [ ] `detect_injection` + `sanitize` для контента из внешних источников/RAG.

**Инструменты (least privilege)**
- [ ] Allowlist инструментов (`safe_to_act`); опасные — только с подтверждением (7.3).
- [ ] MCP-гейты: аутентификация, права, изоляция на сервере инструментов (6.5).

**Вход/выход**
- [ ] Фильтрация входа и выхода; ограничение формата ответа.
- [ ] Не отдавать модели секреты/прод-доступы (11.1).

**Человек и тестирование**
- [ ] Human-in-the-loop на необратимом/критичном (7.3).
- [ ] Adversarial-тесты (red-team) и регрессии (7.5); sandbox для self-host (4.5).

## Применение (код)

```python
from injection_defense import safe_to_act
verdict = safe_to_act({"tool": "read"}, allowlist={"read", "search"}, context_text=rag_chunk)
if not verdict["allowed"]:
    block_and_log(verdict["reason"])
```

## Важно

Полного решения нет — это **свойство природы LLM** (LLM01). Цель — снизить вероятность и ограничить ущерб (least-privilege + человек), а не «выключить» риск. Сигнатурный детект обходится перефразировкой — он лишь один слой.
