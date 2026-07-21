from skill_loader import parse_skill, validate_skill, match_skill

SAMPLE = (
    "---\n"
    "name: editor\n"
    "description: Редактирует текст сокращает чистит и меняет тон письма\n"
    "---\n"
    "# editor\nтело инструкции\n"
)


def test_parse_extracts_frontmatter_and_body():
    p = parse_skill(SAMPLE)
    assert p["name"] == "editor"
    assert "Редактирует текст" in p["description"]
    assert p["body"].startswith("# editor")


def test_parse_without_frontmatter():
    p = parse_skill("просто текст без frontmatter")
    assert p["name"] is None
    assert p["body"] == "просто текст без frontmatter"


def test_validate_flags_missing_and_short():
    assert validate_skill({"name": None, "description": None})
    short = validate_skill({"name": "x", "description": "коротко"})
    assert any("короткий" in p for p in short)
    assert validate_skill(parse_skill(SAMPLE)) == []


def test_match_picks_relevant_skill():
    skills = [
        parse_skill(SAMPLE),
        {"name": "calc", "description": "считает арифметику числа и проценты"},
    ]
    assert match_skill("отредактируй текст письма", skills)["name"] == "editor"
    assert match_skill("посчитай проценты", skills)["name"] == "calc"
    assert match_skill("погода завтра", skills) is None      # нет совпадений
