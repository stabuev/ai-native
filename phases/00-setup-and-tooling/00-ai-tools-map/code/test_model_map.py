from model_map import REGISTRY, Task, recommend, estimate_cost, by_name


def test_registry_sorted_and_priced():
    tiers = [m.tier for m in REGISTRY]
    assert tiers == sorted(tiers)                       # от дешёвого к топовому
    assert all(m.price_in > 0 and m.price_out > 0 for m in REGISTRY)


def test_high_complexity_goes_top():
    m, _ = recommend(Task(complexity="high"))
    assert m.tier == 4
    m2, _ = recommend(Task(needs_code=True))
    assert m2.name == "Claude Opus 4.8"


def test_cheap_for_simple_mass():
    m, _ = recommend(Task(complexity="low", high_volume=True))
    assert m.name == "Gemini Flash"
    assert m.tier == 1


def test_default_is_workhorse():
    m, _ = recommend(Task())
    assert m.name == "Claude Sonnet 4.6"


def test_cost_monotonic_by_tier():
    cheap = estimate_cost(by_name("Claude Haiku 4.5"), 1000, 500)
    pricey = estimate_cost(by_name("Claude Opus 4.8"), 1000, 500)
    assert pricey > cheap


def test_deepseek_is_open_weight_cheap_option():
    ds = by_name("DeepSeek V4-Flash")
    assert ds.tier == 1
    assert "open-weight/self-host" in ds.good_for
    # дешевле дефолтной рабочей лошадки
    assert estimate_cost(ds, 1000, 500) < estimate_cost(by_name("Claude Sonnet 4.6"), 1000, 500)
