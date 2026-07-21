import pytest

from conventions import STUB_MARKERS, numbering_problems, scaffold_lesson, validate_lesson


def test_scaffold_creates_only_required_material(tmp_path):
    base = scaffold_lesson(tmp_path, "99-demo", "01-demo-lesson", "99.1", "Демо")
    assert (base / "docs" / "ru.md").is_file()
    assert not (base / "code").exists()
    assert not (base / "outputs").exists()


def test_validate_flags_unfilled_stub(tmp_path):
    base = scaffold_lesson(tmp_path, "99-demo", "01-demo-lesson", "99.1", "Демо")
    problems = validate_lesson(base)
    assert any("стаба" in problem for problem in problems)
    text = (base / "docs" / "ru.md").read_text(encoding="utf-8")
    assert all(marker in text for marker in STUB_MARKERS)


def test_validate_passes_purposeful_lesson_without_standard_sections_or_artifact(tmp_path):
    base = scaffold_lesson(tmp_path, "99-demo", "01-demo-lesson", "99.1", "Демо")
    (base / "docs" / "ru.md").write_text(
        "# Урок 99.1 · Демо\n\n"
        "**Результат урока:** выбрать подход из двух и обосновать решение.\n\n"
        "Сравни два сценария, выбери вариант и проверь решение по трём критериям.\n",
        encoding="utf-8",
    )
    assert validate_lesson(base) == []


def test_validate_requires_lesson_title(tmp_path):
    base = tmp_path / "lesson"
    (base / "docs").mkdir(parents=True)
    (base / "docs" / "ru.md").write_text("Заполненный текст без заголовка", encoding="utf-8")
    assert any("заголовка" in problem for problem in validate_lesson(base))


def test_numbering_uses_phase_prefix_and_lesson_order_prefix():
    assert numbering_problems("04-skills", "03-projects", "4.3") == []
    assert numbering_problems("04-skills", "04-projects", "4.3") == [
        "папка урока должна начинаться с 03- для урока 4.3"
    ]


def test_scaffold_rejects_mismatched_lesson_prefix(tmp_path):
    with pytest.raises(ValueError, match="начинаться с 03-"):
        scaffold_lesson(tmp_path, "04-skills", "04-projects", "4.3", "Проекты")
