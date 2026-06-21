"""Цены 2026 и за что платишь: калькулятор стоимости — Build It для урока 9.1.

Без зависимостей. Считает стоимость запроса по токенам ввода/вывода с учётом
prompt caching (кэшированный вход дешевле) и batch API (−50%). Платишь за токены,
а не за запросы — поэтому стоимость надо уметь считать ДО отправки.
"""

# Цены 2026, $ за 1M токенов (вход, выход). См. README, «Карта моделей и цен».
PRICES = {
    "gemini-flash": (0.30, 2.50),
    "haiku-4.5": (1.00, 5.00),
    "gpt-5.x": (2.50, 15.00),
    "sonnet-4.6": (3.00, 15.00),
    "opus-4.8": (5.00, 25.00),
}

CACHE_DISCOUNT = 0.1     # кэшированный вход ≈ 10% от цены (−90%)
BATCH_DISCOUNT = 0.5     # batch API ≈ −50%


def cost(model, n_in, n_out, cached_in=0, batch=False):
    """Стоимость одного вызова в $.

    cached_in — сколько входных токенов взяты из кэша (дешевле).
    batch — пакетный режим (−50%).
    """
    if model not in PRICES:
        raise KeyError(f"нет цены для модели: {model}")
    p_in, p_out = PRICES[model]
    fresh_in = max(0, n_in - cached_in)
    total = (fresh_in * p_in + cached_in * p_in * CACHE_DISCOUNT + n_out * p_out) / 1e6
    return total * (BATCH_DISCOUNT if batch else 1.0)


def compare(models, n_in, n_out):
    """Стоимость одного запроса по моделям, по возрастанию."""
    return sorted(((m, round(cost(m, n_in, n_out), 6)) for m in models), key=lambda x: x[1])


if __name__ == "__main__":
    print("Запрос 1000/500 токенов:")
    for m, c in compare(PRICES, 1000, 500):
        print(f"  {m:<14} ${c:.5f}")
    base = cost("sonnet-4.6", 10000, 500)
    print(f"\nSonnet 10k/500: ${base:.5f}")
    print(f"  с кэшем 8k:   ${cost('sonnet-4.6', 10000, 500, cached_in=8000):.5f}")
    print(f"  batch:        ${cost('sonnet-4.6', 10000, 500, batch=True):.5f}")
