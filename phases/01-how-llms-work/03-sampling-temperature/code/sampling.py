"""Учебный сэмплер одного токена для урока 1.3.

Код делает явным офлайн-конвейер:
logits -> softmax(temperature) -> top-k -> top-p -> weighted sample.

Это контракт учебного алгоритма, а не копия внутренней реализации конкретного API.
"""

import math
import random


def _argmax(values):
    """Вернуть позицию первого максимума в непустой последовательности."""
    if not values:
        raise ValueError("values must not be empty")
    return max(range(len(values)), key=lambda index: values[index])


def softmax(logits, temperature=1.0):
    """Преобразовать непустые logits в вероятности при temperature > 0."""
    if not logits:
        raise ValueError("logits must not be empty")
    if temperature <= 0:
        raise ValueError("softmax temperature must be greater than zero")

    maximum = max(logits)
    weights = [math.exp((logit - maximum) / temperature) for logit in logits]
    total = sum(weights)
    return [weight / total for weight in weights]


def _renormalize(probs):
    """Проверить веса и вернуть их копию с суммой 1."""
    if not probs:
        raise ValueError("probabilities must not be empty")
    if any(probability < 0 for probability in probs):
        raise ValueError("probabilities must be non-negative")

    total = sum(probs)
    if total <= 0:
        raise ValueError("probabilities must have a positive sum")
    return [probability / total for probability in probs]


def top_k_filter(probs, k):
    """Оставить k наибольших позиций и вернуть нормализованную копию."""
    normalized = _renormalize(probs)
    if k is None:
        return normalized
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError("k must be a positive integer or None")
    if k >= len(normalized):
        return normalized

    order = sorted(
        range(len(normalized)),
        key=lambda index: normalized[index],
        reverse=True,
    )
    keep = set(order[:k])
    filtered = [
        probability if index in keep else 0.0
        for index, probability in enumerate(normalized)
    ]
    return _renormalize(filtered)


def top_p_filter(probs, p):
    """Оставить минимальное ядро с исходной суммарной массой не меньше p."""
    normalized = _renormalize(probs)
    if p is None:
        return normalized
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not 0 < p <= 1:
        raise ValueError("p must be in the interval (0, 1] or None")
    if p == 1:
        return normalized

    order = sorted(
        range(len(normalized)),
        key=lambda index: normalized[index],
        reverse=True,
    )
    keep = set()
    cumulative = 0.0
    for index in order:
        keep.add(index)
        cumulative += normalized[index]
        if cumulative >= p:
            break

    filtered = [
        probability if index in keep else 0.0
        for index, probability in enumerate(normalized)
    ]
    return _renormalize(filtered)


def sample(logits, temperature=1.0, top_k=None, top_p=None, rng=None):
    """Вернуть индекс, выбранный по явно заданному учебному конвейеру."""
    if not logits:
        raise ValueError("logits must not be empty")
    if temperature < 0:
        raise ValueError("temperature must not be negative")
    if temperature == 0:
        return _argmax(logits)

    probs = softmax(logits, temperature)
    probs = top_k_filter(probs, top_k)
    probs = top_p_filter(probs, top_p)

    generator = rng if rng is not None else random
    draw = generator.random()
    cumulative = 0.0
    for index, probability in enumerate(probs):
        cumulative += probability
        if draw <= cumulative:
            return index

    # Защита от накопленной ошибки float: возвращаем последнюю ненулевую позицию.
    return max(index for index, probability in enumerate(probs) if probability > 0)


if __name__ == "__main__":
    example_logits = [3.0, 2.0, 1.0, 0.0]

    print("temperature distributions")
    for value in (0.5, 1.0, 2.0):
        distribution = softmax(example_logits, value)
        print(f"T={value}: {[round(probability, 3) for probability in distribution]}")

    base = softmax(example_logits)
    print("top_k=2:", [round(value, 3) for value in top_k_filter(base, 2)])
    print("top_p=.8:", [round(value, 3) for value in top_p_filter(base, 0.8)])
    print("T=0 index:", sample(example_logits, temperature=0))

    first_rng = random.Random(7)
    second_rng = random.Random(7)
    first_sequence = [sample(example_logits, rng=first_rng) for _ in range(8)]
    second_sequence = [sample(example_logits, rng=second_rng) for _ in range(8)]
    print("seeded sequence A:", first_sequence)
    print("seeded sequence B:", second_sequence)
