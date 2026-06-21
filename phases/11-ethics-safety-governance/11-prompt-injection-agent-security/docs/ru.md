# Урок 11.5 · Prompt injection и безопасность агентов

**Фаза 11 — Этика, безопасность, governance** · **Результат фазы:** Оценить риски, настроить приватность и написать политику использования ИИ.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** Данные из недоверенных источников — это код для модели; их инструкции нельзя выполнять вслепую.

## PROBLEM

LLM не отличает «инструкции» от «данных» — обе идут одним каналом. Поэтому веб-страница, письмо или документ из RAG могут содержать **скрытую команду**, которая перехватывает агента (**prompt injection**, **RAG-poisoning**). Для агента с инструментами это критично: injection ведёт к «excessive agency» — выполнению опасных действий. Это **№1 риск OWASP LLM Top 10 (LLM01)**.

## CONCEPT

```
недоверенные данные (веб/письмо/RAG-чанк)
   │ могут содержать: "ignore previous… exfiltrate…"
   ▼
detect_injection → sanitize → tool allowlist → human на критичном
   (defense-in-depth: ни один слой не достаточен сам по себе)
```

Полного решения нет (природа LLM), поэтому — **эшелонированная защита**: детект + санитизация + least-privilege инструменты + человек на критичных действиях (7.3).

## BUILD IT

Демо prompt injection / RAG-poisoning + базовая защита: [`code/injection_defense.py`](../code/injection_defense.py).

- `detect_injection(text)` — маркеры инъекций (RU+EN);
- `sanitize(text)` — нейтрализация в недоверенных данных;
- `tool_allowed` / `safe_to_act(action, allowlist, context)` — блок при инъекции в контексте или инструменте вне allowlist.

```bash
python code/injection_defense.py
pytest code -q
```

Тест: детект EN/RU, sanitize маскирует, `safe_to_act` блокирует RAG-poisoning и инструмент вне allowlist. ⚠️ Детект по сигнатурам — нижняя граница (обходится перефразировкой); это слой, а не серебряная пуля.

## USE IT

Защита в проде (мульти-инструмент):

- **OWASP LLM01** — чек-лист: разделять данные/инструкции, ограничивать привилегии, фильтровать вход/выход, human-in-the-loop на чувствительном, adversarial-тесты.
- **MCP-гейты** — на сервере инструментов (Ф6): allowlist, аутентификация, изоляция; не отдавать модели опасные операции.
- **Runtime-guardrails** — input/output tripwire (OpenAI Agents SDK guardrails, урок 7.3), least-privilege инструментов, sandbox для self-host агентов (4.5).
- Связь: приватность (11.1), guardrails/HITL (7.3), поломки агентов (7.4).

## SHIP IT

**Артефакт:** Чек-лист защиты от prompt injection → [`outputs/prompt-injection-checklist.md`](../outputs/prompt-injection-checklist.md)

Практический чек-лист (по OWASP LLM01): что фильтровать, какие allowlist, где человек, как тестировать. Завершает Фазу 11 на стороне agent security.

## Материалы

- [OWASP — Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) — LLM01 Prompt Injection и др.
- [OWASP — Top 10 for LLMs 2025 (PDF)](https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-v2025.pdf) — описание и митигации.
- [Anthropic — Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — guardrails и ограничение автономии.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
