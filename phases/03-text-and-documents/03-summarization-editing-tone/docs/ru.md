# Урок 3.1 · Резюмирование, редактура, тон

**Фаза 3 — Текст и документы** · **Результат фазы:** Строить пайплайны резюмирования и редактуры; собрать базовый RAG над своим корпусом.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** Текст обрабатывают конвейером: сжать → почистить → задать тон.

## PROBLEM

Большая часть работы — это текст: длинные письма, отчёты, переписка. «Сделай покороче и поприличнее» одним махом ненадёжно: то смысл потеряется, то тон не тот. Нужен **конвейер** с раздельными стадиями, которые можно настраивать и проверять по отдельности.

## CONCEPT

```
сырой текст → [черновик/резюме] → [редактура] → [тон] → готово
                 что важно            убрать лишнее   под аудиторию
```

Разделение стадий = контроль: каждую можно менять и оценивать независимо (мост к eval, урок 2.5). Это тот же приём декомпозиции из 2.3, но для текста.

## BUILD IT

Текстовый пайплайн «черновик → редактура → тон», без зависимостей: [`code/editing_pipeline.py`](../code/editing_pipeline.py).

- `summarize_extractive(text, n)` — extractive-резюме по частоте значимых слов;
- `tighten(text)` — убрать слова-филлеры и лишние пробелы;
- `set_tone(text, tone)` — заменить маркеры тона (formal/casual);
- `run_pipeline(text, stages)` — собрать стадии в конвейер.

```bash
python code/editing_pipeline.py
pytest code -q
```

Стадии офлайн и детерминированы; в проде каждую заменяет вызов модели, но контракт «текст → текст» тот же.

## USE IT

Те же стадии — промптами к модели на реальных документах/переписке (мульти-провайдер):

```python
def stage(instruction, text, model="claude-sonnet-4-6"):
    p = f"{instruction}\n\nТекст:\n{text}"
    return Anthropic().messages.create(model=model, max_tokens=600,
        messages=[{"role": "user", "content": p}]).content[0].text
    # OpenAI:  OpenAI().responses.create(model="gpt-5.x", input=p).output_text
    # Google:  genai.Client().models.generate_content(model="gemini-2.x-flash", contents=p).text

draft = stage("Сожми в 3 пункта", document)
edited = stage("Сделай короче и яснее, убери воду", draft)
final = stage("Перепиши в деловом тоне", edited)
```

## SHIP IT

**Артефакт:** Редакторский skill → [`outputs/editor/`](../outputs/editor/SKILL.md)

Скилл `editor` (черновик → редактура → тон) с настраиваемыми стадиями; зарегистрирован в [`.claude/skills/editor`](../../../.claude/skills/editor/SKILL.md). Дальше масштабируем на длинные документы — урок 3.2.

## Материалы

- [Anthropic — Prompting best practices](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices) — приёмы для качественных текстовых задач.
- [Anthropic — Prompt engineering overview](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview) — обзор техник.
- [anthropics/prompt-eng-interactive-tutorial](https://github.com/anthropics/prompt-eng-interactive-tutorial) — практика на примерах.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
