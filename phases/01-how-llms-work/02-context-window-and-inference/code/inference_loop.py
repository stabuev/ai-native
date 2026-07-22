"""Наблюдаемый autoregressive inference-loop для урока 1.2.

Таблица ``model`` заменяет нейросеть только на одной границе:
видимый контекст -> распределение следующего токена. Это позволяет изучить
сам цикл генерации, не добавляя отдельную задачу обучения игрушечной модели.
"""


def visible_context(context, window):
    """Вернуть последние ``window`` токенов новым списком."""
    if window <= 0:
        raise ValueError("window must be positive")
    return list(context[-window:])


def greedy_next_token(probabilities):
    """Вернуть токен с наибольшей вероятностью."""
    if not probabilities:
        raise ValueError("probabilities must not be empty")
    return max(probabilities, key=probabilities.get)


def generate(model, prompt, max_new_tokens, window, stop_token="<STOP>"):
    """Сгенерировать токены жадным выбором и вернуть подробную трассу.

    ``model`` — словарь вида ``{tuple(context): {token: probability}}``.
    Stop-токен фиксируется в трассе, но не входит в пользовательские tokens.
    """
    if max_new_tokens < 0:
        raise ValueError("max_new_tokens must be non-negative")

    context = list(prompt)
    tokens = []
    trace = []

    for step in range(1, max_new_tokens + 1):
        current_context = visible_context(context, window)
        probabilities = model.get(tuple(current_context))

        if not probabilities:
            return {
                "tokens": tokens,
                "trace": trace,
                "stop_reason": "no_distribution",
            }

        chosen_token = greedy_next_token(probabilities)
        trace.append(
            {
                "step": step,
                "visible_context": current_context,
                "probabilities": dict(probabilities),
                "chosen_token": chosen_token,
            }
        )

        if chosen_token == stop_token:
            return {
                "tokens": tokens,
                "trace": trace,
                "stop_reason": "stop_token",
            }

        tokens.append(chosen_token)
        context.append(chosen_token)

    return {
        "tokens": tokens,
        "trace": trace,
        "stop_reason": "max_new_tokens",
    }


if __name__ == "__main__":
    toy_model = {
        ("remember", "blue"): {"sky": 0.9, "sea": 0.1},
        ("blue",): {"sky": 0.2, "sea": 0.8},
        ("blue", "sky"): {"<STOP>": 1.0},
        ("sky",): {"<STOP>": 1.0},
        ("sea",): {"<STOP>": 1.0},
    }
    prompt = ["remember", "blue"]

    for context_window in (2, 1):
        result = generate(
            toy_model,
            prompt,
            max_new_tokens=3,
            window=context_window,
        )
        print(f"window={context_window}: {result}")
