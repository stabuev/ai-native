# Урок 4.3 · Проекты и рабочие пространства

**Фаза 4 — Скиллы, память и проекты** · **Результат фазы:** Упаковывать способности в SKILL.md, хранить контекст в памяти и собирать рабочие проекты.

> **MOTTO.** Проект = постоянная инструкция + база знаний: ассистент перестаёт начинать «с нуля».

## PROBLEM

Универсальный чат не знает твоего контекста: каждый раз объясняешь роль, правила и подкладываешь документы. **Проект** (workspace) фиксирует system prompt и базу знаний один раз — и ассистент отвечает «как член твоей команды» во всех диалогах. Соберём такой проект сами.

## CONCEPT

```
Project
 ├─ system_prompt   постоянная роль и правила
 ├─ knowledge[]     база знаний проекта
 └─ build_context(query):
        system_prompt + retrieve(query, k) + запрос  → промпт модели
```

Это объединение фазы: **скилл** (способность) + **память** (что помним) + **RAG** (что нашли) внутри одного рабочего пространства.

## BUILD IT

Проект «system prompt + база знаний» с retrieval: [`code/project.py`](../code/project.py).

- `Project(name, system_prompt, knowledge)` — рабочее пространство;
- `add_knowledge(doc)` — пополнить базу;
- `retrieve(query, k)` / `build_context(query, k)` — найти релевантное и собрать промпт.

```bash
python code/project.py
pytest code -q
```

Тест показывает суть: в контекст попадает system prompt и **только релевантные** куски знаний (нерелевантное отсекается — экономия окна, урок 4.4).

## USE IT

Те же «проекты» есть во всех платформах (мульти-провайдер):

- **Claude Projects** — workspace с инструкциями и knowledge base (RAG включается автоматически).
- **Custom GPTs** (OpenAI) — name + instructions + knowledge + capabilities, собирается в билдере.
- **Gemini Gems** — кастомный ассистент с инструкциями и файлами знаний.

Везде одно: постоянная инструкция + загруженные документы → ассистент под конкретную задачу без повторных объяснений.

## SHIP IT

**Артефакт:** Настроенный ассистент с базой знаний → [`outputs/assistant-project.md`](../outputs/assistant-project.md)

Рецепт сборки проекта: что класть в system prompt, как структурировать knowledge, как проверять качество ответов. Дальше — управление контекстом проекта (4.4) и превращение в агента (Фаза 7).

## Материалы

- [Claude — Projects](https://www.anthropic.com/news/projects) — workspace с инструкциями и базой знаний.
- [OpenAI — Creating and editing GPTs](https://help.openai.com/en/articles/8554397-creating-and-editing-gpts) — сборка Custom GPT.
- [Google — Gems tips](https://blog.google/products/gemini/google-gems-tips/) — кастомные ассистенты Gemini.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
