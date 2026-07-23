"""Мягкая структурная проверка уроков AI Native.

Валидатор намеренно не оценивает педагогическое качество и не требует одинаковых
секций, кода, квиза или артефакта. Он ловит только базовые структурные ошибки:
отсутствующий материал, неверную нумерацию и следы незаполненного шаблона.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
from collections.abc import Iterable


STUB_MARKERS = (
    "<id>",
    "<название>",
    "<outcome>",
    "<наблюдаемое действие",
    "<что уже освоено>",
    "<где результат понадобится>",
    "<Связный учебный переход",
    "<n>",
)

LESSON_HEADING = re.compile(r"# Урок\s+(\d+)\.(\d+)\b")


def numbering_problems(lesson_path: str | Path, lesson_id: str) -> list[str]:
    """Сопоставить id ``phase.lesson`` с именами каталогов ``PP-*`` и ``LL-*``."""
    path = Path(lesson_path)
    match = re.fullmatch(r"(\d+)\.(\d+)", lesson_id)
    if not match:
        return [f"некорректный id урока: {lesson_id!r}; ожидается <phase>.<lesson>"]

    phase, lesson = (int(part) for part in match.groups())
    problems = []
    if not path.parent.name.startswith(f"{phase:02d}-"):
        problems.append(
            f"папка фазы должна начинаться с {phase:02d}- для урока {lesson_id}"
        )
    if not path.name.startswith(f"{lesson:02d}-"):
        problems.append(
            f"папка урока должна начинаться с {lesson:02d}- для урока {lesson_id}"
        )
    return problems


def validate_lesson(lesson_path: str | Path) -> list[str]:
    """Проверить заполненность и нумерацию одного урока."""
    path = Path(lesson_path)
    doc = path / "docs" / "ru.md"
    if not doc.is_file():
        return ["нет docs/ru.md"]

    text = doc.read_text(encoding="utf-8").strip()
    problems = []
    if not text:
        return ["пустой docs/ru.md"]

    heading = LESSON_HEADING.match(text)
    if heading is None:
        problems.append("в docs/ru.md нет корректного заголовка '# Урок <N.N> …'")
    else:
        lesson_id = ".".join(heading.groups())
        problems.extend(numbering_problems(path, lesson_id))

    found_markers = [marker for marker in STUB_MARKERS if marker in text]
    if found_markers:
        problems.append(
            "в docs/ru.md остались маркеры незаполненного шаблона: "
            + ", ".join(found_markers)
        )
    return problems


def discover_lessons(phases_root: str | Path = "phases") -> list[Path]:
    """Найти каталоги уроков в дереве ``phases/PP-*/LL-*``."""
    root = Path(phases_root)
    if not root.is_dir():
        return []
    return sorted(
        lesson
        for phase in root.iterdir()
        if phase.is_dir()
        for lesson in phase.iterdir()
        if lesson.is_dir() and re.match(r"\d{2}-", lesson.name)
    )


def validate_paths(paths: Iterable[str | Path]) -> dict[Path, list[str]]:
    """Вернуть только уроки с найденными структурными проблемами."""
    return {
        Path(path): problems
        for path in paths
        if (problems := validate_lesson(path))
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Проверить базовую структуру уроков AI Native"
    )
    parser.add_argument(
        "lessons",
        nargs="*",
        help="каталоги уроков; без аргументов проверяются все phases/*/*",
    )
    args = parser.parse_args(argv)
    lessons = [Path(path) for path in args.lessons] or discover_lessons()
    if not lessons:
        parser.error("не найдено ни одного урока для проверки")

    failures = validate_paths(lessons)
    if failures:
        for lesson, problems in failures.items():
            for problem in problems:
                print(f"{lesson}: {problem}")
        return 1

    print(f"OK: проверено уроков — {len(lessons)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
