"""Traceable chunking and hierarchical reduction for lesson 3.2.

The word-based splitter is deliberately small: it exposes boundaries, overlap,
and provenance without pretending to parse paragraphs, tables, or PDF layout.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def _positive_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def chunk_text(text, size=100, overlap=20, source="document"):
    """Split text into overlapping word chunks with positional metadata.

    ``word_start`` is inclusive and ``word_end`` is exclusive.  The returned
    records are suitable for inspection and for carrying source identity into
    later map/reduce or retrieval stages.
    """
    size = _positive_int(size, "size")
    if isinstance(overlap, bool) or not isinstance(overlap, int):
        raise ValueError("overlap must be a non-negative integer smaller than size")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must satisfy 0 <= overlap < size")
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be a non-empty string")

    words = text.split()
    if not words:
        return []

    step = size - overlap
    chunks = []
    for index, start in enumerate(range(0, len(words), step)):
        end = min(start + size, len(words))
        chunks.append(
            {
                "id": f"{source}#chunk-{index:04d}",
                "source": source,
                "index": index,
                "word_start": start,
                "word_end": end,
                "text": " ".join(words[start:end]),
            }
        )
        if end == len(words):
            break
    return chunks


def map_chunks(chunks, map_fn):
    """Apply ``map_fn`` to every chunk and preserve chunk provenance."""
    mapped = []
    for chunk in chunks:
        result = map_fn(chunk["text"])
        if not isinstance(result, str) or not result.strip():
            raise ValueError(f"map_fn returned empty text for {chunk['id']}")
        mapped.append(
            {
                "id": f"summary:{chunk['id']}",
                "chunk_ids": [chunk["id"]],
                "level": 0,
                "text": result,
            }
        )
    return mapped


def _balanced_batches(items: list[dict], fan_in: int) -> Iterable[list[dict]]:
    """Balance a level; a singleton is possible only when it cannot be avoided."""
    batch_count = (len(items) + fan_in - 1) // fan_in
    base, larger_batches = divmod(len(items), batch_count)
    start = 0
    for index in range(batch_count):
        batch_size = base + (1 if index < larger_batches else 0)
        yield items[start:start + batch_size]
        start += batch_size


def hierarchical_reduce(mapped, reduce_fn, fan_in=4):
    """Reduce mapped records in bounded batches and return the full trace.

    ``reduce_fn`` receives a list of two to ``fan_in`` texts.  Each reduced
    record carries all original ``chunk_ids``.  For an empty input, ``result``
    is ``None`` and no reduce call is made.
    """
    fan_in = _positive_int(fan_in, "fan_in")
    if fan_in < 2:
        raise ValueError("fan_in must be at least 2")

    current = [dict(item) for item in mapped]
    if not current:
        return {"result": None, "levels": []}

    levels = [current]
    level = 1
    while len(current) > 1:
        reduced = []
        for batch_index, batch in enumerate(_balanced_batches(current, fan_in)):
            if len(batch) == 1:
                carried = dict(batch[0])
                carried.update(
                    {
                        "id": f"carry-l{level}-b{batch_index:04d}",
                        "level": level,
                        "carried_from": batch[0]["id"],
                    }
                )
                reduced.append(carried)
                continue
            result = reduce_fn([item["text"] for item in batch])
            if not isinstance(result, str) or not result.strip():
                raise ValueError(
                    f"reduce_fn returned empty text at level {level}, "
                    f"batch {batch_index}"
                )
            reduced.append(
                {
                    "id": f"reduce-l{level}-b{batch_index:04d}",
                    "chunk_ids": [
                        chunk_id
                        for item in batch
                        for chunk_id in item["chunk_ids"]
                    ],
                    "level": level,
                    "text": result,
                }
            )
        current = reduced
        levels.append(current)
        level += 1

    return {"result": current[0], "levels": levels}


def map_reduce(chunks, map_fn, reduce_fn, fan_in=4):
    """Map chunks, then reduce them hierarchically with a bounded fan-in."""
    return hierarchical_reduce(
        map_chunks(chunks, map_fn),
        reduce_fn,
        fan_in=fan_in,
    )


if __name__ == "__main__":
    demo_text = " ".join(f"w{i}" for i in range(1, 26))
    demo_chunks = chunk_text(
        demo_text,
        size=6,
        overlap=2,
        source="demo-report",
    )

    print("Chunks:")
    for chunk in demo_chunks:
        print(
            f"  {chunk['id']} "
            f"[{chunk['word_start']}:{chunk['word_end']}] "
            f"{chunk['text']}"
        )

    observed_batch_sizes = []

    def demo_map(text):
        words = text.split()
        return f"{words[0]}…{words[-1]}"

    def demo_reduce(parts):
        observed_batch_sizes.append(len(parts))
        return " | ".join(parts)

    trace = map_reduce(
        demo_chunks,
        demo_map,
        demo_reduce,
        fan_in=3,
    )
    print("Records by level:", [len(level) for level in trace["levels"]])
    print("Reduce batch sizes:", observed_batch_sizes)
    print("Final chunk IDs:", trace["result"]["chunk_ids"])
