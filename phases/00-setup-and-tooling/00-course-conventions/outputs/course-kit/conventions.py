"""Соглашения курса: scaffolder + валидатор урока — Build It для урока 0.4.

Без зависимостей. `scaffold_lesson()` создаёт дерево урока
phases/<NN>/<lesson>/{code,docs,outputs} и стаб docs/ru.md по 6 шагам.
`validate_lesson()` проверяет, что урок отвечает Definition of Done (структура,
все секции в ru.md, тест test_*.py, непустой артефакт в outputs/).
"""
from __future__ import annotations
from pathlib import Path

# Секции, обязательные в docs/ru.md (MOTTO — отдельной строкой-цитатой).
SECTIONS = ("PROBLEM", "CONCEPT", "BUILD IT", "USE IT", "SHIP IT")

STUB_TEMPLATE = """# Урок {id} · {title}

> **MOTTO.** _<идея урока в одну строку>_

## PROBLEM
_<конкретная боль>_

## CONCEPT
_<интуиция, диаграмма>_

## BUILD IT
_<механизм с нуля в `code/` + тест>_

## USE IT
_<то же через реальный инструмент/API>_

## SHIP IT
**Артефакт:** _<из колонки Ship It>_ → `outputs/`

---
**DoD:** код запускается, тест зелёный, ru.md заполнен. _(стаб — заполнить через /lesson-author {id})_
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

    code = base / "code"
    py = list(code.glob("*.py")) if code.exists() else []
    if not py:
        problems.append("нет кода в code/")
    elif not any(p.name.startswith("test_") for p in py):
        problems.append("нет теста test_*.py в code/")

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
