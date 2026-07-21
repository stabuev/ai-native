from spec import Metric, CapstoneSpec, is_measurable, validate_spec


def _good_spec():
    return CapstoneSpec(
        goal="Автоматизировать разбор обращений",
        metrics=[Metric("время", baseline=10.0, target=3.0, unit="мин")],
        budget_usd=200.0,
    )


def test_complete_spec_passes():
    assert validate_spec(_good_spec()) == []


def test_missing_goal_flagged():
    spec = _good_spec()
    spec.goal = ""
    assert "нет цели" in validate_spec(spec)


def test_missing_budget_flagged():
    spec = _good_spec()
    spec.budget_usd = None
    assert "не задан бюджет" in validate_spec(spec)


def test_unmeasurable_metric_flagged():
    spec = CapstoneSpec(goal="цель", metrics=[Metric("качество")], budget_usd=100.0)
    assert any("измерим" in p for p in validate_spec(spec))


def test_is_measurable():
    assert is_measurable(Metric("m", baseline=1, target=2))
    assert not is_measurable(Metric("m", baseline=1))
