# Урок 3.2 · Длинный контекст и работа с файлами

**Фаза 3 — Текст и документы** · **Результат фазы:** Строить пайплайны резюмирования и редактуры; собрать базовый RAG над своим корпусом.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** Документ не влезает в окно — режь на части, сжимай каждую, своди вместе.

## PROBLEM

Отчёт на 200 страниц не влезает в контекстное окно (урок 1.2), а если и влезает (1M токенов) — это дорого и «середина теряется». Нужна стратегия: разбить документ на куски, обработать каждый и собрать общий результат — **chunking + map-reduce**.

## CONCEPT

```
длинный документ
   │ chunking (перекрывающиеся куски)
   ▼
[chunk] [chunk] [chunk] ...
   │ map: сжать каждый кусок
   ▼
[summary] [summary] [summary]
   │ reduce: свести в один результат
   ▼
итоговое резюме
```

Перекрытие (`overlap`) сохраняет связность на стыках. Map-reduce масштабируется на документы любой длины и кладётся в основу RAG (урок 3.3).

## BUILD IT

Chunking с перекрытием + map-reduce, без зависимостей: [`code/chunking.py`](../code/chunking.py).

- `chunk_text(text, size, overlap)` — резать на куски по словам внахлёст (валидирует `overlap < size`);
- `map_reduce(chunks, map_fn, reduce_fn)` — обработать каждый кусок и свести результаты.

```bash
python code/chunking.py
pytest code -q
```

Тесты проверяют главное: ни одно слово не теряется, соседние чанки реально перекрываются, map-reduce корректно сводит.

## USE IT

В проде `map_fn` — суммаризация куска моделью, `reduce_fn` — сведение саммари; либо грузишь файл целиком в длинное окно:

```python
chunks = chunk_text(big_doc, size=800, overlap=100)
summarize = lambda c: Anthropic().messages.create(model="claude-haiku-4-5", max_tokens=200,
    messages=[{"role": "user", "content": f"Сожми кусок:\n{c}"}]).content[0].text
final = map_reduce(chunks, summarize,
    lambda parts: stage_reduce("\n".join(parts)))   # свести саммари в одно
```

Альтернатива для умеренных объёмов — длинный контекст напрямую: загрузка PDF/таблиц и окно до 1M токенов (Claude/Gemini), с подсказками из [long context tips](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips): данные — вверх, вопрос — в конец.

## SHIP IT

**Артефакт:** Пайплайн обработки длинных документов → [`outputs/long-doc-pipeline.md`](../outputs/long-doc-pipeline.md)

Рецепт «когда chunking+map-reduce, когда длинное окно» + параметры (size/overlap) под типы документов. Связка с RAG — урок 3.3, с бюджетом — урок 1.1.

## Материалы

- [Anthropic — Long context prompting tips](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips) — как работать с большим окном.
- [LangChain — Text splitters](https://docs.langchain.com/oss/python/integrations/splitters) — стратегии chunking (recursive, по токенам, по структуре).
- [Anthropic — Prompting long context (research)](https://www.anthropic.com/research/prompting-long-context) — почему позиция данных важна.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
