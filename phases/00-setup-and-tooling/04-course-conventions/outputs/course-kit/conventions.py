"""Scaffolder и мягкий структурный валидатор урока — Build It для урока 0.4.

Без зависимостей. `scaffold_lesson()` создаёт только обязательный `docs/ru.md` с
минимальным паспортом. `validate_lesson()` проверяет наличие заголовка и отсутствие
следов незаполненного стаба. Секции, код, квиз и артефакт намеренно не требуются:
их целесообразность определяется педагогическим контрактом.
"""
from __future__ import annotations

from pathlib import Path
import re


STUB_MARKERS = (
    "<наблюдаемое действие",
    "<что уже освоено>",
    "<где результат понадобится>",
    "<Связный учебный переход",
    "(стаб — заполнить",
)

STUB_TEMPLATE = """# Урок {id} · {title}

**Результат урока:** после урока студент сможет <наблюдаемое действие + критерий качества>.
**Опора:** <что уже освоено> · **Дальше:** <где результат понадобится>

<Связный учебный переход; выбери только целесообразные секции>

---
**DoD:** результат доказан; структура целесообразна; соразмерные проверки зелёные. (стаб — заполнить через /lesson-author {id})
"""


def numbering_problems(phase_dir: str, lesson_dir: str, lesson_id: str) -> list[str]:
    """Проверить PP фазы и LL урока относительно id вида ``phase.lesson``."""
    match = re.fullmatch(r"(\d+)\.(\d+)", lesson_id)
    if not match:
        return [f"некорректный id урока: {lesson_id!r}; ожидается <phase>.<lesson>"]
    phase, lesson = (int(part) for part in match.groups())
    problems = []
    if not phase_dir.startswith(f"{phase:02d}-"):
        problems.append(
            f"папка фазы должна начинаться с {phase:02d}- для урока {lesson_id}"
        )
    if not lesson_dir.startswith(f"{lesson:02d}-"):
        problems.append(
            f"папка урока должна начинаться с {lesson:02d}- для урока {lesson_id}"
        )
    return problems


def scaffold_lesson(root, phase_dir: str, lesson_dir: str, lesson_id: str, title: str) -> Path:
    """Создать обязательный docs/ru.md. Возвращает путь к уроку."""
    problems = numbering_problems(phase_dir, lesson_dir, lesson_id)
    if problems:
        raise ValueError("; ".join(problems))
    base = Path(root) / "phases" / phase_dir / lesson_dir
    docs = base / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    doc = docs / "ru.md"
    if not doc.exists():
        doc.write_text(STUB_TEMPLATE.format(id=lesson_id, title=title), encoding="utf-8")
    return base


def validate_lesson(lesson_path) -> list[str]:
    """Проверить только заполненность материала, не его педагогическую достаточность."""
    doc = Path(lesson_path) / "docs" / "ru.md"
    if not doc.exists():
        return ["нет docs/ru.md"]

    text = doc.read_text(encoding="utf-8").strip()
    problems = []
    if not text:
        problems.append("пустой docs/ru.md")
    if not text.startswith("# Урок "):
        problems.append("в docs/ru.md нет заголовка '# Урок …'")
    else:
        match = re.match(r"# Урок\s+(\d+\.\d+)\b", text)
        if match:
            problems.extend(numbering_problems(doc.parent.parent.parent.name, doc.parent.parent.name, match.group(1)))
    if any(marker in text for marker in STUB_MARKERS):
        problems.append("в docs/ru.md остались маркеры незаполненного стаба")
    return problems


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        lesson = scaffold_lesson(tmp, "99-demo", "01-demo-lesson", "99.1", "Демо-урок")
        print("Создан урок:", lesson.relative_to(tmp))
        print("Проверка свежего стаба:", validate_lesson(lesson))
