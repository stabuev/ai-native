# Урок 7.3 · Human-in-the-loop и guardrails

**Фаза 7 — Agent Engineering** · **Результат фазы:** Собрать надёжного агента с памятью, планированием, human-in-the-loop и guardrails.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** Автономность без заслонов опасна: критичные действия — через подтверждение и валидацию.

## PROBLEM

Агент, который сам жмёт «удалить», «перевести деньги», «задеплоить», однажды сделает это по галлюцинации или prompt-инъекции. Нужны **guardrails**: валидация аргументов до исполнения и **human-in-the-loop** — пауза на подтверждение для необратимых действий. Это разница между «помощником» и «миной».

## CONCEPT

```
действие агента
   │ 1) валидаторы (типы, лимиты, разрешённые операции)
   │ 2) опасное? → пауза → подтверждение человека (approve/reject)
   │ 3) известный инструмент?
   ▼ только тогда — исполнение
```

Безопасные действия идут без трения; опасные (delete/send/deploy) останавливаются и ждут человека. Валидаторы ловят «плохие» аргументы ещё до подтверждения.

## BUILD IT

Точки подтверждения + валидация действий: [`code/guardrails.py`](../code/guardrails.py).

- `requires_confirmation(tool)` — опасные инструменты (delete/send_money/deploy…);
- `run_action(action, tools, confirm, validators)` — валидация → подтверждение → исполнение;
- `amount_limit(max)` — пример валидатора (лимит суммы).

```bash
python code/guardrails.py
pytest code -q
```

Тесты: безопасное действие исполняется без трения; опасное без подтверждения — блок; `confirm=False` — блок; перевод сверх лимита — блок валидатором.

## USE IT

Контроль агента на критичных шагах — готовыми механизмами (мульти-провайдер):

- **OpenAI Agents SDK** — `guardrails` (input/output/tool tripwire) + **human-in-the-loop**: `needs_approval` на инструменте, пауза с `RunState`, `approve()/reject()`, resume.
- **Anthropic** — tool use с подтверждением на стороне приложения; разрешения в Claude Code/Agent SDK.
- Паттерн: дешёвый guardrail-модель отсекает плохое до дорогого вызова; необратимое — только после approve.

## SHIP IT

**Артефакт:** Шаблон guardrails → [`outputs/guardrails-template.md`](../outputs/guardrails-template.md)

Готовый шаблон: список опасных действий, валидаторы, точки подтверждения, аудит. Дальше: что делать, когда агент всё равно ломается (7.4).

## Материалы

- [OpenAI — Guardrails (Agents SDK)](https://openai.github.io/openai-agents-python/guardrails/) — input/output/tool проверки.
- [OpenAI — Human-in-the-loop](https://openai.github.io/openai-agents-python/human_in_the_loop/) — пауза и approve/reject.
- [Anthropic — Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — guardrails и тестирование в песочнице.

---
**Часы:** ~5 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
