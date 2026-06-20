# Урок 0.4 · Соглашения курса

**Фаза 0 — Setup & Tooling** · **Результат фазы:** Настроить окружение, ключи и агента; осознанно выбрать модель под задачу.

> **MOTTO.** Единый формат урока — чтобы код, разбор и артефакт всегда лежали на своих местах.

## PROBLEM

Когда у каждого урока своя раскладка, репозиторий превращается в свалку: непонятно, где код, где разбор, где готовый артефакт, а проверить «урок готов или нет» можно только глазами. На 52 урока это смертельно. Нужен **общий контракт** структуры и автоматическая проверка Definition of Done.

## CONCEPT

Каждый урок — это тройка папок и цикл из 6 шагов:

```
phases/<NN>-<phase>/<NN>-<lesson>/
├── code/      Build It (с нуля) + Use It + тест test_*.py
├── docs/ru.md разбор по 6 шагам: MOTTO·PROBLEM·CONCEPT·BUILD IT·USE IT·SHIP IT
└── outputs/   артефакт: prompt · skill · agent · MCP
```

**Definition of Done** урока: `docs/ru.md` со всеми секциями, рабочий код с проходящим `test_*.py`, непустой `outputs/`. Это можно и нужно проверять программой.

## BUILD IT

Scaffolder + валидатор урока с нуля, без зависимостей: [`code/conventions.py`](../code/conventions.py).

- `scaffold_lesson(root, phase_dir, lesson_dir, id, title)` — создаёт дерево `code/docs/outputs` и стаб `docs/ru.md` со всеми 6 шагами;
- `validate_lesson(path)` — возвращает список нарушений DoD (нет секции, нет теста, пустой `outputs/`).

```bash
python code/conventions.py
pytest code -q
```

Демо создаёт демо-урок во временной папке и тут же проверяет: свежий стаб «не готов» (нет кода и артефакта) — ровно как и должно быть до наполнения.

## USE IT

Те же соглашения уже автоматизированы скиллом курса — `/lesson-author <id>` (см. [`.claude/skills/lesson-author`](../../../.claude/skills/lesson-author/SKILL.md)):

```
/lesson-author 2.3     # находит урок в README, заводит папки, пишет стаб ru.md,
                       # ведёт по Build It / Use It / Ship It и прогоняет pytest
```

Цикл сдачи урока: `scaffold` → наполнить → `validate_lesson` зелёный → отметить `[x]` в `PROGRESS.md` → коммит **после всей фазы**.

## SHIP IT

**Артефакт:** Заготовка репозитория курса → [`outputs/course-kit/`](../outputs/course-kit/)

Мини-кит для старта своего курса/репозитория в этом формате: `conventions.py` (scaffolder + валидатор) и `CONVENTIONS.md` (контракт структуры и DoD). Тот же валидатор можно повесить в CI, чтобы «незаконченные» уроки не проходили проверку.

## Материалы

- [pytest — Get started](https://docs.pytest.org/en/stable/getting-started.html) — как писать и запускать тесты урока.
- [Agent Skills — overview](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) — механика скиллов, на которой стоит `/lesson-author`.
- [ai-engineering-from-scratch](https://github.com/stabuev/ai-engineering-from-scratch) — образец каркаса «фазы → уроки → артефакты».

---
**Часы:** ~2 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
