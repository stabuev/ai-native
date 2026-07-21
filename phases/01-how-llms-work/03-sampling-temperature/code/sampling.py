"""Сэмплирование: temperature, top-k, top-p — Build It для урока 1.3.

Без зависимостей (math, random). Превращает логиты в распределение и выбирает
следующий токен. temperature=0 → детерминированный argmax; top-k и top-p
ограничивают множество кандидатов. Тот же механизм крутит любая LLM при генерации.
"""
import math
import random


def softmax(logits, temperature=1.0):
    """Логиты → вероятности. temperature<=0 → one-hot на argmax (детерминизм)."""
    if temperature <= 0:
        m = max(range(len(logits)), key=lambda i: logits[i])
        return [1.0 if i == m else 0.0 for i in range(len(logits))]
    mx = max(logits)                                   # сдвиг для устойчивости exp
    exps = [math.exp((l - mx) / temperature) for l in logits]
    s = sum(exps)
    return [e / s for e in exps]


def _renorm(probs):
    s = sum(probs)
    return [p / s for p in probs] if s > 0 else probs[:]


def top_k_filter(probs, k):
    """Оставить k самых вероятных, остальное обнулить и перенормировать."""
    if not k or k <= 0 or k >= len(probs):
        return probs[:]
    keep = set(sorted(range(len(probs)), key=lambda i: probs[i], reverse=True)[:k])
    return _renorm([p if i in keep else 0.0 for i, p in enumerate(probs)])


def top_p_filter(probs, p):
    """Nucleus: оставить минимальный набор по убыванию, чья сумма >= p."""
    if p is None or p >= 1.0:
        return probs[:]
    order = sorted(range(len(probs)), key=lambda i: probs[i], reverse=True)
    keep, cum = set(), 0.0
    for i in order:
        keep.add(i)
        cum += probs[i]
        if cum >= p:
            break
    return _renorm([pr if i in keep else 0.0 for i, pr in enumerate(probs)])


def sample(logits, temperature=1.0, top_k=None, top_p=None, rng=None):
    """Выбрать индекс следующего токена. temperature=0 → argmax (детерминизм)."""
    if temperature <= 0:
        return max(range(len(logits)), key=lambda i: logits[i])
    probs = softmax(logits, temperature)
    probs = top_k_filter(probs, top_k)
    probs = top_p_filter(probs, top_p)
    rng = rng or random
    r, cum = rng.random(), 0.0
    for i, pr in enumerate(probs):
        cum += pr
        if r <= cum:
            return i
    return len(probs) - 1


def entropy(probs):
    """Энтропия распределения (мера «разброса»)."""
    return -sum(p * math.log(p) for p in probs if p > 0)


if __name__ == "__main__":
    logits = [3.0, 2.0, 1.0, 0.0]
    for t in (0.0, 0.5, 1.0, 2.0):
        p = softmax(logits, t)
        print(f"T={t}: probs={[round(x,3) for x in p]} entropy={entropy(p):.3f}")
    print("top_k=2 :", [round(x, 3) for x in top_k_filter(softmax(logits), 2)])
    print("top_p=.5:", [round(x, 3) for x in top_p_filter(softmax(logits), 0.5)])
    rng = random.Random(42)
    print("samples :", [sample(logits, 1.0, rng=rng) for _ in range(8)])
