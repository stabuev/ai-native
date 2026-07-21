from skill_runtime import Runtime, parse_skill, EDITOR_SKILL, CALC_SKILL


def _rt():
    rt = Runtime()
    rt.load(EDITOR_SKILL, handler=lambda m: "сокращено")
    rt.load(CALC_SKILL, handler=lambda m: "42")
    return rt


def test_parse_skill():
    s = parse_skill(EDITOR_SKILL)
    assert s["name"] == "editor"
    assert "редактирует" in s["description"]


def test_load_registers_skills():
    rt = _rt()
    assert set(rt.skills) == {"editor", "calc"}


def test_route_picks_relevant_skill():
    rt = _rt()
    assert rt.route("отредактируй текст письма") == "editor"
    assert rt.route("посчитай проценты") == "calc"
    assert rt.route("прогноз погоды") is None


def test_handle_executes_and_remembers():
    rt = _rt()
    res = rt.handle("отредактируй текст письма")
    assert res["skill"] == "editor" and res["result"] == "сокращено"
    rt.handle("посчитай проценты")
    assert len(rt.memory) == 2          # память между сообщениями


def test_handle_no_skill():
    assert _rt().handle("прогноз погоды")["skill"] is None
