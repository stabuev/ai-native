from pathlib import Path

from course_validation import (
    discover_lessons,
    main,
    numbering_problems,
    validate_lesson,
)


def _write_lesson(root: Path, phase: str, lesson: str, heading: str) -> Path:
    lesson_path = root / "phases" / phase / lesson
    docs = lesson_path / "docs"
    docs.mkdir(parents=True)
    (docs / "ru.md").write_text(heading, encoding="utf-8")
    return lesson_path


def test_validate_accepts_filled_lesson_with_matching_number(tmp_path):
    lesson = _write_lesson(
        tmp_path,
        "01-demo",
        "02-example",
        "# Урок 1.2 · Пример\n\n**Результат урока:** выполнить действие.",
    )
    assert validate_lesson(lesson) == []


def test_validate_flags_missing_material_and_template_markers(tmp_path):
    missing = tmp_path / "phases" / "01-demo" / "01-missing"
    assert validate_lesson(missing) == ["нет docs/ru.md"]

    stub = _write_lesson(
        tmp_path,
        "01-demo",
        "02-stub",
        "# Урок 1.2 · <название>\n\n<Связный учебный переход>",
    )
    problems = validate_lesson(stub)
    assert any("маркеры незаполненного шаблона" in problem for problem in problems)


def test_numbering_must_match_phase_and_lesson_directories(tmp_path):
    lesson = tmp_path / "phases" / "01-demo" / "03-example"
    assert numbering_problems(lesson, "1.2") == [
        "папка урока должна начинаться с 02- для урока 1.2"
    ]


def test_discovery_and_cli_validate_selected_lessons(tmp_path, capsys):
    lesson = _write_lesson(
        tmp_path,
        "03-demo",
        "01-example",
        "# Урок 3.1 · Пример\n\nСвязный материал.",
    )
    assert discover_lessons(tmp_path / "phases") == [lesson]
    assert main([str(lesson)]) == 0
    assert "OK: проверено уроков — 1" in capsys.readouterr().out
