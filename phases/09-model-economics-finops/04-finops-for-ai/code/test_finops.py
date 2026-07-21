from finops import Ledger, roi


def _ledger():
    led = Ledger()
    led.record(0.02, team="analytics", model="sonnet-4.6", cache_hit=False)
    led.record(0.002, team="analytics", model="haiku-4.5", cache_hit=True)
    led.record(0.05, team="support", model="opus-4.8", cache_hit=False)
    return led


def test_total():
    assert _ledger().total() == 0.072


def test_by_team_aggregation():
    by_team = _ledger().by_tag("team")
    assert by_team["analytics"] == 0.022
    assert by_team["support"] == 0.05


def test_by_model_aggregation():
    assert _ledger().by_tag("model")["opus-4.8"] == 0.05


def test_cache_hit_rate():
    assert _ledger().cache_hit_rate() == round(1 / 3, 3)


def test_over_budget():
    led = _ledger()
    assert led.over_budget(0.05) is True
    assert led.over_budget(1.0) is False


def test_roi():
    # было 100, стало 20 (экономия 80) + выгода 50 = 130; / 20 = 6.5
    assert roi(100, 20, 50) == 6.5
