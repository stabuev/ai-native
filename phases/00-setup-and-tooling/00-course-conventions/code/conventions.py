"""Соглашения курса: scaffolder + валидатор урока — Build It для урока 0.4.

Без зависимостей. `scaffold_lesson()` создаёт дерево урока
phases/<NN>/<lesson>/{code,docs,outputs} и стаб docs/ru.md по 6 шагам.
`validate_lesson()` проверяет Definition of Done: docs/ru.md со всеми секциями и
непустой артефакт в outputs/. Код и тест — по необходимости урока (концептуальные
уроки бывают без code/), поэтому их отсутствие нарушением не считается.
"""
from __future__ import annotations
from pathlib import Path

# Секции, обязательные в docs/ru.md (MOTTO — отдельной строкой-цитатой).
SECTIONS = ("PROBLEM", "CONCEPT", "BUILD IT", "USE IT", "SHIP IT")

STUB_TEMPLATE = """# Урок {id} · {title}

> **MOTTO.** <идея урока в одну строку>

## PROBLEM
<конкретная боль>

## CONCEPT
<интуиция, диаграмма>

## BUILD IT
<механизм с нуля в `code/`, если урок его требует; иначе обзорно>

## USE IT
<то же через реальный инструмент/API>

## SHIP IT
**Артефакт:** <из колонки Ship It> → `outputs/`

---
**DoD:** ru.md заполнен, артефакт на месте (код запускается и тест зелёный — если урок их предполагает). (стаб — заполнить через /lesson-author {id})
"""


def scaffold_lesson(root, phase_dir: str, lesson_dir: str, lesson_id: str, title: str) -> Path:
    """Создать папки урока и стаб docs/ru.md. Возвращает путь к уроку."""
    base = Path(root) / "phases" / phase_dir / lesson_dir
    for sub in ("code", "docs", "outputs"):
        (base / sub).mkdir(parents=True, exist_ok=True)
    doc = base / "docs" / "ru.md"
    if not doc.exists():
        doc.write_text(STUB_TEMPLATE.format(id=lesson_id, title=title), encoding="utf-8")
    return base


def validate_lesson(lesson_path) -> list[str]:
    """Список нарушений DoD (пустой список = урок готов по структуре)."""
    base = Path(lesson_path)
    problems = []

    doc = base / "docs" / "ru.md"
    if not doc.exists():
        problems.append("нет docs/ru.md")
    else:
        text = doc.read_text(encoding="utf-8")
        for sec in SECTIONS:
            if sec not in text:
                problems.append(f"в docs/ru.md нет секции {sec}")

    # Код и тест не обязательны: концептуальные уроки бывают без code/,
    # а тест добавляем там, где он осмыслен (см. CLAUDE.md, Definition of Done).

    out = base / "outputs"
    artifacts = [p for p in out.glob("*") if p.name != ".gitkeep"] if out.exists() else []
    if not artifacts:
        problems.append("пустой outputs/ (нет артефакта)")

    return problems


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        lesson = scaffold_lesson(tmp, "99-demo", "99-demo-lesson", "9.9", "Демо-урок")
        print("Создан урок:", lesson.relative_to(tmp))
        print("Проверка свежего стаба:", validate_lesson(lesson))
