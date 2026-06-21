# Урок 0.3 · Агент и SkillKit

**Фаза 0 — Setup & Tooling** · **Результат фазы:** Настроить окружение, ключи и агента; осознанно выбрать модель под задачу.

> **MOTTO.** Агент + скиллы превращают модель из «чата» в рабочий инструмент с памятью навыков.

## PROBLEM

Голая модель в чате забывает контекст и не умеет твоих приёмов. Агент (Claude Code / Cursor / Codex) живёт в твоём репозитории, видит файлы и запускает команды — но без **скиллов** каждый раз объясняешь одно и то же заново. И ещё: курс на 200 часов нельзя проходить вслепую — нужно понять, что пролистать, а на чём сфокусироваться.

## CONCEPT

**Скилл** — это переиспользуемый навык в виде папки с `SKILL.md` (frontmatter `name`/`description` + инструкция). Агент видит описание и подхватывает скилл, когда задача под него подходит.

```
агент (Claude Code / Cursor / Codex)
   └── .claude/skills/<name>/SKILL.md   ← навык: когда применять + как
          /find-your-level      → входной квиз → персональный маршрут
          /check-understanding  → квиз по фазе → что повторить
```

В этом уроке мы и собираем два курсовых скилла как настоящие артефакты, и заодно понимаем механику скиллов изнутри (детально — Фаза 4).

## BUILD IT

Два офлайн-движка без зависимостей:

- [`code/find_your_level.py`](../code/find_your_level.py) — входной квиз: 10 вопросов с весами → `score()` → `level()` (Новичок/Практик/Инженер) → `route()` строит план по 13 фазам с действием (focus/skim/skip) и оценкой часов.
- [`code/check_understanding.py`](../code/check_understanding.py) — квиз по фазе: `run_quiz(phase, answers)` считает результат, даёт вердикт и список уроков на повтор (банк для Фазы 1 как образец).

```bash
python code/find_your_level.py
python code/check_understanding.py
pytest code -q
```

Новичок получает полные ~200 ч, инженер — ~178 ч (пропускает setup, листает базу). Это и есть «персональный маршрут».

## USE IT

1. Поставь агента: **Claude Code** (`npm i -g @anthropic-ai/claude-code`), Cursor или Codex.
2. Положи курсовые скиллы в `.claude/skills/` (они уже в репозитории) — агент подхватит их по описанию.
3. Запусти онбординг прямо в агенте:

```
/find-your-level            → ответь на 10 вопросов → получишь маршрут с часами
/check-understanding 1       → после Фазы 1 → узнаешь, что повторить
```

Скиллы кросс-платформенны: тот же `SKILL.md` понимают Claude Code, Cursor и Codex.

> **Врезка (2026): категории кодовых агентов.** Claude Code — терминал и глубокий контекст; Cursor — IDE и инлайн-редактирование; Codex — облачный фоновый воркер; OpenClaw / Hermes — локальные персональные платформы (подробно в уроке 4.5). У каждого свой файл-инструкция проекта: `CLAUDE.md` (Claude Code), `AGENTS.md` (Codex), `.cursorrules` (Cursor) — но формат скиллов `SKILL.md` у них общий.

## SHIP IT

**Артефакт:** Персональный маршрут с оценкой часов → [`outputs/personal-route.md`](../outputs/personal-route.md)

Плюс два рабочих скилла: [`.claude/skills/find-your-level`](../../../.claude/skills/find-your-level/SKILL.md) и [`.claude/skills/check-understanding`](../../../.claude/skills/check-understanding/SKILL.md). Маршрут — твой личный план прохождения курса; `/check-understanding` возвращается после ключевых фаз (1, 4, 8).

## Материалы

- [Claude Code — overview](https://code.claude.com/docs/en/overview) — агент в терминале, IDE и десктопе.
- [Agent Skills — overview](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) — что такое `SKILL.md` и как он подгружается.
- [anthropics/skills](https://github.com/anthropics/skills) — публичные скиллы и `template-skill` для старта.

---
**Часы:** ~2 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
