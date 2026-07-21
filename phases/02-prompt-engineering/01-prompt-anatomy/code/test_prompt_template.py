from prompt_template import build_prompt, lint_prompt, HEADERS


def test_task_is_always_present():
    p = build_prompt("сделай X")
    assert HEADERS["task"] in p and "сделай X" in p


def test_optional_blocks_render_when_given():
    p = build_prompt("сделай X", role="ты аналитик", output_format="JSON",
                     examples=[("вход", "выход")])
    for key in ("role", "task", "output_format", "examples"):
        assert HEADERS[key] in p
    assert "вход" in p and "выход" in p


def test_lint_flags_missing_blocks():
    bare = build_prompt("только задача")
    missing = lint_prompt(bare)
    assert "role" in missing and "context" in missing and "examples" in missing
    assert "task" not in missing


def test_lint_passes_full_prompt():
    full = build_prompt("задача", role="r", context="c", output_format="f",
                        examples=[("i", "o")])
    assert lint_prompt(full) == []
