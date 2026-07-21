"""Длинный контекст: chunking + map-reduce — Build It для урока 3.2.

Без зависимостей. Длинный документ не влезает в контекстное окно (урок 1.2):
режем его на перекрывающиеся чанки, обрабатываем каждый (map) и сводим
результаты (reduce). Перекрытие сохраняет связность на стыках.
"""


def chunk_text(text, size=100, overlap=20):
    """Резать текст на чанки по словам: `size` слов, `overlap` слов внахлёст."""
    if size <= 0:
        raise ValueError("size должен быть > 0")
    if overlap >= size:
        raise ValueError("overlap должен быть < size")
    words = text.split()
    if not words:
        return []
    step = size - overlap
    chunks = []
    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start:start + size]))
        if start + size >= len(words):
            break
    return chunks


def map_reduce(chunks, map_fn, reduce_fn):
    """Применить map_fn к каждому чанку, затем reduce_fn к списку результатов.

    Это паттерн map-reduce суммаризации: сжать части, потом свести их вместе.
    """
    mapped = [map_fn(c) for c in chunks]
    return reduce_fn(mapped)


if __name__ == "__main__":
    text = " ".join(f"слово{i}" for i in range(1, 26))   # 25 слов
    chunks = chunk_text(text, size=10, overlap=3)
    print(f"{len(chunks)} чанк(ов):")
    for c in chunks:
        print("  ", c)
    # map: длина чанка; reduce: суммарно слов (с учётом перекрытий)
    total = map_reduce(chunks, lambda c: len(c.split()), sum)
    print("Слов суммарно по чанкам (с перекрытием):", total)
