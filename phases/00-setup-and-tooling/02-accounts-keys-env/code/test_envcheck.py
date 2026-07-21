from envcheck import parse_env, validate


def test_parse_ignores_comments_and_handles_export_quotes():
    text = """
    # comment line
    export ANTHROPIC_API_KEY="sk-ant-abc"   # inline comment
    OPENAI_API_KEY = sk-xyz
    EMPTY=
    """
    env = parse_env(text)
    assert env["ANTHROPIC_API_KEY"] == "sk-ant-abc"
    assert env["OPENAI_API_KEY"] == "sk-xyz"
    assert env["EMPTY"] == ""
    assert "comment line" not in env


def test_validate_detects_missing_and_placeholder():
    env = {"ANTHROPIC_API_KEY": "your-key-here"}
    problems = validate(env, ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"])
    assert any("ANTHROPIC_API_KEY" in p and "плейсхолдер" in p for p in problems)
    assert any("OPENAI_API_KEY" in p and "отсутствует" in p for p in problems)


def test_validate_detects_bad_prefix():
    problems = validate({"ANTHROPIC_API_KEY": "wrong-prefix"}, ["ANTHROPIC_API_KEY"])
    assert problems and "префикс" in problems[0]


def test_validate_passes_good_keys():
    env = {"ANTHROPIC_API_KEY": "sk-ant-ok", "OPENAI_API_KEY": "sk-ok", "GOOGLE_API_KEY": "AIza..."}
    assert validate(env, list(env)) == []
