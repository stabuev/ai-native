from metrics import improvement, roi, before_after, competency_report


def test_improvement_lower_is_better():
    assert improvement(10, 3, lower_is_better=True) == 70.0      # время −70%
    assert improvement(0.50, 0.10, lower_is_better=True) == 80.0  # стоимость −80%


def test_improvement_higher_is_better():
    assert improvement(70, 88, lower_is_better=False) == 25.7     # качество +25.7%


def test_roi():
    # экономия 800 + выгода 300 = 1100; / 200 = 5.5
    assert roi(before_cost=1000, after_cost=200, value_gained=300) == 5.5


def test_before_after_structure():
    ba = before_after({"t": 10}, {"t": 5}, {"t": True})
    assert ba["t"]["improvement_pct"] == 50.0
    assert ba["t"]["before"] == 10 and ba["t"]["after"] == 5


def test_competency_report():
    rep = competency_report({"промпты": True, "агенты": True, "MCP": False})
    assert rep["done"] == 2 and rep["total"] == 3
    assert "MCP" in rep["missing"]
