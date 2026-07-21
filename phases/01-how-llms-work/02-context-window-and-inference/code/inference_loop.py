"""Учебный inference-loop + контекстное окно — Build It для урока 1.2.

Без зависимостей. Показывает, что inference — это цикл: модель раз за разом
предсказывает следующий токен по предыдущим и дописывает его в контекст.
Модель здесь игрушечная (n-граммы с backoff по маленькому корпусу), но механизм
тот же, что у LLM. Контекстное окно — сколько последних токенов модель видит:
что вышло за окно, для модели «исчезает».
"""
from collections import defaultdict, Counter


def train_ngram(corpus, order=3):
    """Для каждого суффикса длины 1..order — распределение следующего токена."""
    counts = defaultdict(Counter)
    for seq in corpus:
        for i in range(len(seq)):
            for n in range(1, order + 1):
                if i - n >= 0:
                    counts[tuple(seq[i - n:i])][seq[i]] += 1
    model = {}
    for ctx, c in counts.items():
        total = sum(c.values())
        model[ctx] = {tok: n / total for tok, n in c.items()}
    return model


def next_token_probs(model, context, order=3):
    """Распределение по самому длинному суффиксу контекста (до order), что есть в модели.

    Это backoff: нет длинного совпадения — отступаем к более короткому.
    """
    for n in range(min(order, len(context)), 0, -1):
        ctx = tuple(context[-n:])
        if ctx in model:
            return model[ctx]
    return {}


def generate(model, prompt, max_tokens=10, window=8, order=3):
    """Жадная авторегрессия: на каждом шаге берём самый вероятный next-token.

    `window` — контекстное окно: модель видит только последние `window` токенов.
    """
    context = list(prompt)
    out = []
    for _ in range(max_tokens):
        visible = context[-window:]                  # контекстное окно
        probs = next_token_probs(model, visible, order)
        if not probs:
            break                                    # нечего предсказать — стоп
        nxt = max(probs, key=probs.get)              # greedy = argmax
        out.append(nxt)
        context.append(nxt)
    return out


if __name__ == "__main__":
    corpus = [
        ["the", "cat", "sat", "on", "the", "mat"],
        ["the", "cat", "ate", "the", "fish"],
        ["a", "dog", "sat", "on", "the", "rug"],
    ]
    model = train_ngram(corpus, order=3)
    print("Контекст ['the','cat'] →", next_token_probs(model, ["the", "cat"]))
    print("generate(['the','cat']) →", generate(model, ["the", "cat"], max_tokens=4))
    print("Окно=1, ['a','dog','sat'] →", generate(model, ["a", "dog", "sat"], 3, window=1))
