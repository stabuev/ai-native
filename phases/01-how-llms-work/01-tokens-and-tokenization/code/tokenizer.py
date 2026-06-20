"""Мини-токенизатор (BPE) с нуля — Build It для урока 1.1.

Без внешних зависимостей. Учит merge-правила на маленьком корпусе,
кодирует текст в токены и декодирует обратно. Цель — понять, что
токен != слово и != символ, а результат алгоритма слияния пар.
"""
from collections import Counter

END = "</w>"  # маркер конца слова


def _words(corpus):
    """Корпус -> {слово как кортеж символов + END: частота}."""
    vocab = Counter()
    for line in corpus:
        for word in line.split():
            vocab[tuple(list(word) + [END])] += 1
    return vocab


def _merge(word, pair):
    """Слить все вхождения пары (a, b) в одном слове."""
    a, b = pair
    out, i = [], 0
    while i < len(word):
        if i < len(word) - 1 and word[i] == a and word[i + 1] == b:
            out.append(a + b)
            i += 2
        else:
            out.append(word[i])
            i += 1
    return tuple(out)


def train_bpe(corpus, num_merges):
    """Выучить список merge-правил по частоте соседних пар."""
    vocab = _words(corpus)
    merges = []
    for _ in range(num_merges):
        pairs = Counter()
        for word, freq in vocab.items():
            for i in range(len(word) - 1):
                pairs[(word[i], word[i + 1])] += freq
        if not pairs:
            break
        best = max(pairs, key=pairs.get)
        merges.append(best)
        vocab = {_merge(w, best): f for w, f in vocab.items()}
    return merges


def encode(text, merges):
    """Текст -> список токенов с применением выученных merge-правил."""
    tokens = []
    for word in text.split():
        symbols = tuple(list(word) + [END])
        for pair in merges:
            symbols = _merge(symbols, pair)
        tokens.extend(symbols)
    return tokens


def decode(tokens):
    """Токены -> исходный текст."""
    return "".join(tokens).replace(END, " ").strip()


if __name__ == "__main__":
    corpus = [
        "low lower lowest",
        "newer wider newest",
        "low low low newer newer wider",
    ]
    merges = train_bpe(corpus, num_merges=10)
    print("Выучено merge-правил:", len(merges))
    print("Первые правила:", merges[:5])
    for text in ["low newer", "lowest"]:
        toks = encode(text, merges)
        print(f"\n{text!r}")
        print("  токены:", toks, f"({len(toks)} шт.)")
        print("  без BPE:", len(encode(text, [])), "шт.")
        print("  decode :", repr(decode(toks)))
