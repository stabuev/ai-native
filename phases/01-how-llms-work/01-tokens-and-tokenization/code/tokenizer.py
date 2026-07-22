"""Учебный byte-level BPE для урока 1.1.

Реализация намеренно невелика: UTF-8 текст превращается в отдельные байты,
частые соседние пары байтов сливаются, а выученные правила затем применяются
к новому тексту. Здесь нет pre-tokenization и специальных токенов production-
токенизатора, зато основной механизм BPE и точный round-trip наблюдаемы.
"""
from collections import Counter

Token = bytes
Merge = tuple[Token, Token]


def _byte_tokens(text: str) -> list[Token]:
    """UTF-8 текст -> список однобайтовых токенов."""
    return [bytes([value]) for value in text.encode("utf-8")]


def _merge(tokens: list[Token], pair: Merge) -> list[Token]:
    """Слить все непересекающиеся вхождения пары слева направо."""
    a, b = pair
    out, i = [], 0
    while i < len(tokens):
        if i < len(tokens) - 1 and tokens[i] == a and tokens[i + 1] == b:
            out.append(a + b)
            i += 2
        else:
            out.append(tokens[i])
            i += 1
    return out


def train_bpe(corpus: list[str], num_merges: int) -> list[Merge]:
    """Выучить до ``num_merges`` правил по частоте соседних byte-токенов."""
    if num_merges < 0:
        raise ValueError("num_merges must be non-negative")

    sequences = [_byte_tokens(text) for text in corpus]
    merges: list[Merge] = []
    for _ in range(num_merges):
        pair_counts: Counter[Merge] = Counter()
        for tokens in sequences:
            pair_counts.update(zip(tokens, tokens[1:]))

        if not pair_counts:
            break

        # При равной частоте выбираем лексикографически меньшую пару: один и тот
        # же корпус всегда даёт один и тот же порядок правил.
        best = min(pair_counts, key=lambda pair: (-pair_counts[pair], pair))
        merges.append(best)
        sequences = [_merge(tokens, best) for tokens in sequences]
    return merges


def encode(text: str, merges: list[Merge]) -> list[Token]:
    """Текст -> byte-токены с применением правил в порядке обучения."""
    tokens = _byte_tokens(text)
    for pair in merges:
        tokens = _merge(tokens, pair)
    return tokens


def decode(tokens: list[Token]) -> str:
    """Byte-токены -> исходный UTF-8 текст без потери пробелов и Unicode."""
    return b"".join(tokens).decode("utf-8")


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
