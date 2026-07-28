"""Starter for the offline Build It exercise from lesson 3.4.

Copy this file as ``vector_store.py`` and implement the marked methods.  The
lexical vectorizer and cosine helper are provided: the exercise is about the
state and compatibility contract of a persistent vector store.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
HASH_EMBEDDING_ID = "hash-bow-v1"
HASH_DIMENSION = 512
STOP_WORDS = frozenset(
    {
        "а",
        "без",
        "в",
        "во",
        "для",
        "до",
        "за",
        "и",
        "из",
        "или",
        "к",
        "как",
        "на",
        "не",
        "но",
        "о",
        "об",
        "от",
        "по",
        "с",
        "со",
        "у",
        "что",
        "это",
    }
)


def hash_embed(text: str) -> list[float]:
    """Return a deterministic lexical hashing vector."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    vector = [0.0] * HASH_DIMENSION
    tokens = re.findall(r"\w+", text.lower())
    for token in tokens:
        if token in STOP_WORDS:
            continue
        digest = hashlib.blake2s(token.encode("utf-8"), digest_size=4).digest()
        bucket = int.from_bytes(digest, byteorder="big") % HASH_DIMENSION
        vector[bucket] += 1.0
    return vector


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Return cosine similarity for two dense vectors of equal length."""
    if len(a) != len(b):
        raise ValueError("vectors must have equal dimensions")
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


class VectorStore:
    """Store traceable records and compatible vectors with exact search."""

    def __init__(self, *, embedding_id: str, dimension: int):
        # Validate both arguments, then initialize items and a set of seen IDs.
        raise NotImplementedError

    def __len__(self) -> int:
        return len(self.items)

    def add(self, record: Mapping[str, Any], vector: Sequence[float]) -> None:
        """Validate and append one new record; reject duplicate IDs."""
        raise NotImplementedError

    def query(
        self,
        vector: Sequence[float],
        *,
        k: int = 3,
        min_score: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Return at most k positive matches with all record metadata."""
        raise NotImplementedError

    def to_manifest(self) -> dict[str, Any]:
        """Return schema, embedding metadata and stored items."""
        raise NotImplementedError

    def save(self, path: str | Path) -> None:
        """Write ``to_manifest()`` as UTF-8 JSON."""
        raise NotImplementedError

    @classmethod
    def load(
        cls,
        path: str | Path,
        *,
        embedding_id: str,
        dimension: int,
    ) -> "VectorStore":
        """Validate a manifest and restore it through ``add``."""
        raise NotImplementedError
