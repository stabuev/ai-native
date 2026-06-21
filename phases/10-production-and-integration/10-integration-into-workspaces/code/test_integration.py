from integration import AIFeature, run_pipeline


def _feat(enabled=True):
    return AIFeature(
        fn=lambda t: f"AI:{t}",
        fallback=lambda t: f"FB:{t}",
        enabled=enabled,
    )


def test_enabled_uses_ai():
    assert _feat().run("x") == "AI:x"


def test_disabled_uses_fallback():
    assert _feat(enabled=False).run("x") == "FB:x"


def test_error_falls_back():
    def boom(_):
        raise RuntimeError("down")
    feat = AIFeature(fn=boom, fallback=lambda t: f"FB:{t}")
    assert feat.run("x") == "FB:x"          # прод не падает


def test_pipeline_integrates_ai_step():
    steps = [str.strip, _feat().run, str.upper]
    assert run_pipeline(steps, "  hi ") == "AI:HI"
