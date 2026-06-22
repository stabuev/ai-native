# Урок 2.1 · Анатомия промпта

**Фаза 2 — Промпт-инжиниринг** · **Результат фазы:** Писать воспроизводимые промпты и измерять их качество через eval-harness.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** Промпт — это интерфейс к интеллекту; у хорошего интерфейса есть структура.

## PROBLEM

«Напиши покороче» работает случайно: сегодня ок, завтра мимо. Без структуры промпт невоспроизводим — нельзя понять, что именно повлияло на ответ, и нельзя переиспользовать находку. Нужна **анатомия**: разложить промпт на части, которыми можно управлять.

## CONCEPT

У промпта пять управляемых блоков:

```
[ Роль ]      кто отвечает (эксперт, редактор, парсер)
[ Контекст ]  что нужно знать для задачи
[ Задача ]    что именно сделать  ← единственный обязательный блок
[ Формат ]    как должен выглядеть ответ
[ Примеры ]   few-shot образцы вход→выход (урок 2.2)
```

Чем явнее блоки, тем стабильнее ответ и тем легче его измерять (мост к 2.5). Структуру удобно держать как шаблон с подстановками.

> **Врезка: цикл Description ↔ Discernment (AI Fluency).** Хороший промпт редко выходит с первого раза: ты **описываешь** задачу (Description), **оцениваешь** ответ (Discernment) и уточняешь — и так по кругу. Этот урок — про первую половину (анатомия описания); измерять вторую системно будем в уроке 2.5 (eval-harness).

## BUILD IT

Сборщик промпта из блоков + линтер на полноту: [`code/prompt_template.py`](../code/prompt_template.py).

- `build_prompt(task, role=…, context=…, output_format=…, examples=…)` — собирает промпт; обязателен только `task`;
- `lint_prompt(text)` — какие анатомические блоки отсутствуют.

```bash
python code/prompt_template.py
pytest code -q
```

Линтер делает структуру проверяемой: «голый» промпт сигналит о недостающих ролях/формате — это и есть путь к воспроизводимости.

## USE IT

Один и тот же структурированный промпт — на трёх платформах; сравни, как меняется ответ:

```python
prompt = build_prompt(task="Суммаризируй отзыв в 3 пунктах",
                      role="Ты редактор поддержки", output_format="Маркированный список")
# Anthropic
Anthropic().messages.create(model="claude-sonnet-4-6", max_tokens=300,
    system="Ты редактор поддержки", messages=[{"role": "user", "content": prompt}])
# OpenAI
OpenAI().responses.create(model="gpt-5.x", instructions="Ты редактор поддержки", input=prompt)
# Google
genai.Client().models.generate_content(model="gemini-2.x-flash", contents=prompt)
```

Заметь: «роль» у провайдеров живёт в разных местах (system / instructions / в тексте) — анатомия одна, синтаксис разный.

## SHIP IT

**Артефакт:** Базовый шаблон промпта → [`outputs/prompt-template.md`](../outputs/prompt-template.md)

Переиспользуемый каркас «роль · контекст · задача · формат · примеры» с подстановками. Дальше: примеры → урок 2.2, измерение версий → урок 2.5.

## Материалы

- [Anthropic — Prompt engineering overview](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview) — с чего начать и какие техники есть.
- [Anthropic — Prompting best practices](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices) — живой справочник приёмов.
- [anthropics/prompt-eng-interactive-tutorial](https://github.com/anthropics/prompt-eng-interactive-tutorial) — интерактивный курс по промптингу.

---
**Часы:** ~3 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
