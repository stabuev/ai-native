import pytest
from cost_calculator import cost, compare, PRICES


def test_basic_cost():
    # sonnet 1M вход + 1M выход = 3 + 15 = 18$
    assert cost("sonnet-4.6", 1_000_000, 1_000_000) == 18.0


def test_opus_more_expensive_than_haiku():
    assert cost("opus-4.8", 1000, 500) > cost("haiku-4.5", 1000, 500)


def test_cache_reduces_cost():
    full = cost("sonnet-4.6", 10000, 500)
    cached = cost("sonnet-4.6", 10000, 500, cached_in=8000)
    assert cached < full


def test_batch_halves_cost():
    assert cost("sonnet-4.6", 1000, 500, batch=True) == cost("sonnet-4.6", 1000, 500) / 2


def test_unknown_model_raises():
    with pytest.raises(KeyError):
        cost("gpt-9000", 100, 100)


def test_compare_sorted_cheapest_first():
    ranking = compare(PRICES, 1000, 500)
    assert ranking[0][0] == "gemini-flash"
    assert ranking[-1][0] == "opus-4.8"
