"""Starter for the offline Build It exercise from lesson 3.2.

Copy this file as ``chunking.py`` and implement the four marked functions.
Use only the Python standard library.
"""


def chunk_text(text, size=100, overlap=20, source="document"):
    """Return traceable word chunks with overlap and half-open positions.

    Each record must contain:
    ``id``, ``source``, ``index``, ``word_start``, ``word_end``, and ``text``.
    """
    raise NotImplementedError


def map_chunks(chunks, map_fn):
    """Map every chunk into a non-empty summary record with ``chunk_ids``."""
    raise NotImplementedError


def hierarchical_reduce(mapped, reduce_fn, fan_in=4):
    """Reduce bounded batches; carry an unavoidable singleton without calling reduce."""
    raise NotImplementedError


def map_reduce(chunks, map_fn, reduce_fn, fan_in=4):
    """Compose map_chunks and hierarchical_reduce."""
    raise NotImplementedError


if __name__ == "__main__":
    text = " ".join(f"w{i}" for i in range(1, 26))
    chunks = chunk_text(text, size=6, overlap=2, source="demo-report")
    trace = map_reduce(
        chunks,
        map_fn=lambda part: f"{part.split()[0]}…{part.split()[-1]}",
        reduce_fn=lambda parts: " | ".join(parts),
        fan_in=3,
    )
    print([len(level) for level in trace["levels"]])
    print(trace["result"])
