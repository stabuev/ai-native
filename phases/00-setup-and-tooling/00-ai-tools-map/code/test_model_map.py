from model_map import by_name, estimate_cost


def test_estimate_cost_math():
    flash = by_name("Gemini Flash")
    # 200 вход × 0.30 + 20 выход × 2.50, цены за 1M токенов
    assert abs(estimate_cost(flash, 200, 20) - 0.00011) < 1e-9


def test_batch_10k_tickets():
    # разметка 10 000 тикетов (200/20 токенов на вызов): Flash ≈ $1.10, Opus = $15
    flash = estimate_cost(by_name("Gemini Flash"), 200, 20) * 10_000
    opus = estimate_cost(by_name("Claude Opus 4.8"), 200, 20) * 10_000
    assert abs(flash - 1.10) < 1e-6
    assert abs(opus - 15.00) < 1e-6


def test_pricier_tier_costs_more():
    cheap = estimate_cost(by_name("Claude Haiku 4.5"), 1000, 500)
    pricey = estimate_cost(by_name("Claude Opus 4.8"), 1000, 500)
    assert pricey > cheap
