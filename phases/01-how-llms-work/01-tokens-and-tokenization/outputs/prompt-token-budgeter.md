# Артефакт: prompt-token-budgeter

Оценивает число токенов и стоимость запроса **до** отправки в API. Возвращается во всех фазах; основа для FinOps (Фаза 9).

## Карта цен (2026, $ за 1M токенов)

| Модель | Вход | Выход |
|---|---|---|
| Gemini Flash | 0.30 | — |
| Claude Haiku 4.5 | 1 | 5 |
| GPT-5.x | 2.5 | 15 |
| Claude Sonnet 4.6 | 3 | 15 |
| Claude Opus 4.8 | 5 | 25 |

## Использование

```python
# token_budgeter.py — кладётся рядом и переиспользуется
import tiktoken

PRICES = {  # ($/1M вход, $/1M выход)
    "haiku-4.5": (1, 5),
    "sonnet-4.6": (3, 15),
    "opus-4.8": (5, 25),
    "gpt-5.x": (2.5, 15),
}

def budget(prompt, model="sonnet-4.6", expected_output_tokens=500, enc="o200k_base"):
    n_in = len(tiktoken.get_encoding(enc).encode(prompt))
    p_in, p_out = PRICES[model]
    cost = n_in / 1e6 * p_in + expected_output_tokens / 1e6 * p_out
    return {"input_tokens": n_in, "est_output_tokens": expected_output_tokens,
            "model": model, "est_cost_usd": round(cost, 6)}

if __name__ == "__main__":
    print(budget("Summarize the attached report in 5 bullets.", "haiku-4.5"))
```

## Как переиспользовать

- Перед массовой обработкой прогоняй промпт через `budget()` и сверяй с лимитом.
- Меняй `model`, чтобы увидеть разницу в цене (мост к маршрутизации моделей, Фаза 9).
- Для точности используй токенайзер конкретной модели; учебный BPE из урока — только для интуиции.
