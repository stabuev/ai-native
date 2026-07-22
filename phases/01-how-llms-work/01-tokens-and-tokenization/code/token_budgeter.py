"""Локальная арифметика бюджета запроса без привязки к провайдеру.

Точное или оценочное число входных токенов нужно получить токенизатором
выбранной модели. Актуальные цены студент также передаёт явно, поэтому код не
превращается в устаревающий каталог моделей.
"""
from math import isfinite

TOKENS_PER_MILLION = 1_000_000


def _validate_token_count(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _validate_price(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a non-negative finite number")
    if value < 0 or not isfinite(value):
        raise ValueError(f"{name} must be a non-negative finite number")


def estimate_request_cost(
    input_tokens: int,
    planned_output_tokens: int,
    input_usd_per_million: float,
    output_usd_per_million: float,
) -> dict[str, int | float]:
    """Оценить стоимость по числу токенов и ценам за миллион токенов."""
    _validate_token_count("input_tokens", input_tokens)
    _validate_token_count("planned_output_tokens", planned_output_tokens)
    _validate_price("input_usd_per_million", input_usd_per_million)
    _validate_price("output_usd_per_million", output_usd_per_million)

    input_cost = input_tokens / TOKENS_PER_MILLION * input_usd_per_million
    output_cost = (
        planned_output_tokens / TOKENS_PER_MILLION * output_usd_per_million
    )
    return {
        "input_tokens": input_tokens,
        "planned_output_tokens": planned_output_tokens,
        "input_cost_usd": round(input_cost, 8),
        "planned_output_cost_usd": round(output_cost, 8),
        "estimated_total_usd": round(input_cost + output_cost, 8),
    }


if __name__ == "__main__":
    print(
        estimate_request_cost(
            input_tokens=2_000,
            planned_output_tokens=500,
            input_usd_per_million=3.0,
            output_usd_per_million=15.0,
        )
    )
