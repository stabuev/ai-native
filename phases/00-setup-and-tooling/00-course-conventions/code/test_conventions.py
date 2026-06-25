from conventions import scaffold_lesson, validate_lesson, SECTIONS


def test_scaffold_creates_tree_and_stub(tmp_path):
    base = scaffold_lesson(tmp_path, "99-demo", "99-demo-lesson", "9.9", "Демо")
    assert (base / "code").is_dir()
    assert (base / "docs" / "ru.md").is_file()
    assert (base / "outputs").is_dir()
    text = (base / "docs" / "ru.md").read_text(encoding="utf-8")
    for sec in SECTIONS:
        assert sec in text                      # стаб содержит все 6 шагов


def test_validate_flags_missing_artifact(tmp_path):
    base = scaffold_lesson(tmp_path, "99-demo", "99-demo-lesson", "9.9", "Демо")
    problems = validate_lesson(base)            # ru.md со всеми секциями есть, но outputs/ пуст
    assert any("outputs" in p for p in problems)


def test_validate_passes_conceptual_lesson_without_code(tmp_path):
    # мягкий DoD: достаточно docs/ru.md + артефакта; код/тест не обязательны
    base = scaffold_lesson(tmp_path, "99-demo", "99-demo-lesson", "9.9", "Демо")
    (base / "outputs" / "artifact.md").write_text("# артефакт\n", encoding="utf-8")
    assert validate_lesson(base) == []
