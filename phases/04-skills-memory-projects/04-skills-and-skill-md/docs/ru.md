# Урок 4.1 · Skills и SKILL.md

**Фаза 4 — Скиллы, память и проекты** · **Результат фазы:** Упаковывать способности в SKILL.md, хранить контекст в памяти и собирать рабочие проекты.

> **MOTTO.** Скилл — это навык в виде папки: агент сам подгружает нужный по описанию.

## PROBLEM

Хорошие приёмы (как редактировать, как считать, как оформлять) приходится объяснять агенту заново каждый раз. **Скилл** упаковывает навык в переиспользуемую папку с `SKILL.md`: агент видит описание и сам решает, когда его применить. Без понимания формата и матчинга скиллы кажутся магией.

## CONCEPT

```
.claude/skills/<name>/SKILL.md
   ---
   name: <как зовут>
   description: <когда применять + триггеры>   ← по этому агент выбирает скилл
   ---
   <инструкция: тело, грузится только если скилл выбран>  (progressive disclosure)
```

Ключ — **description с триггерами**: именно по нему агент матчит запрос на скилл, не загружая тело всех скиллов в контекст (экономия — урок 4.4).

## BUILD IT

Парсер SKILL.md + валидатор + матчер, без зависимостей: [`code/skill_loader.py`](../code/skill_loader.py).

- `parse_skill(text)` — разобрать frontmatter (`name`/`description`) и тело (без PyYAML);
- `validate_skill(parsed)` — проверить обязательные поля и длину description;
- `match_skill(query, skills)` — выбрать скилл по пересечению слов запроса и description.

```bash
python code/skill_loader.py
pytest code -q
```

Матчер намеренно простой (совпадение слов) — он показывает суть выбора; настоящий агент матчит **семантически**, поэтому в description важны разные формулировки-триггеры.

## USE IT

Положи скилл в `.claude/skills/<name>/SKILL.md` — Claude Code / Cursor / Codex подхватят его по описанию. Проверка наличия:

```bash
ls .claude/skills/*/SKILL.md          # проектные скиллы
ls ~/.claude/skills/*/SKILL.md        # личные скиллы
```

Тот же `SKILL.md` кросс-платформенный; в курсе так сделаны `editor`, `doc-assistant`, `prompt-eval`, онбординг-скиллы.

## SHIP IT

**Артефакт:** Кросс-платформенный skill → [`outputs/skill-template/`](../outputs/skill-template/SKILL.md)

Готовый шаблон `SKILL.md` (frontmatter + структура тела + чек-лист хорошего description) — копируешь, заполняешь, кладёшь в `.claude/skills/`. Дальше скиллы соединяются с памятью (4.2) и проектами (4.3).

## Материалы

- [Anthropic — Agent Skills overview](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) — что такое скиллы и как грузятся.
- [anthropics/skills](https://github.com/anthropics/skills) — публичные скиллы и `template-skill`.
- [Claude Code — overview](https://code.claude.com/docs/en/overview) — где живут скиллы (`.claude/skills`).

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
