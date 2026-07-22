import math

import pytest

from token_budgeter import estimate_request_cost


def test_estimates_input_output_and_total_cost():
    result = estimate_request_cost(
        input_tokens=250_000,
        planned_output_tokens=100_000,
        input_usd_per_million=2.0,
        output_usd_per_million=5.0,
    )
    assert result["input_cost_usd"] == 0.5
    assert result["planned_output_cost_usd"] == 0.5
    assert result["estimated_total_usd"] == 1.0


def test_zero_usage_has_zero_cost():
    result = estimate_request_cost(0, 0, 3.0, 15.0)
    assert result["estimated_total_usd"] == 0.0


@pytest.mark.parametrize(
    "args",
    [
        (-1, 100, 3.0, 15.0),
        (100, -1, 3.0, 15.0),
        (100, 100, -3.0, 15.0),
        (100, 100, 3.0, math.inf),
    ],
)
def test_rejects_impossible_counts_and_prices(args):
    with pytest.raises(ValueError):
        estimate_request_cost(*args)
