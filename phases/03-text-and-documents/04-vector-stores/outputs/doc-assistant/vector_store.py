"""Persistent vector store used by the lesson 3.4 doc-assistant artifact."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from numbers import Real
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


def _validate_dimension(dimension: int) -> None:
    if isinstance(dimension, bool) or not isinstance(dimension, int) or dimension <= 0:
        raise ValueError("dimension must be a positive integer")


def _normalize_vector(vector: Sequence[float], dimension: int) -> list[float]:
    if isinstance(vector, (str, bytes)) or not isinstance(vector, Sequence):
        raise TypeError("vector must be a sequence of numbers")
    if len(vector) != dimension:
        raise ValueError(
            f"vector dimension {len(vector)} does not match expected {dimension}"
        )

    normalized = []
    for value in vector:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError("vector values must be numbers")
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("vector values must be finite")
        normalized.append(number)
    return normalized


def _normalize_record(record: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        raise TypeError("record must be a mapping")

    try:
        normalized = json.loads(
            json.dumps(dict(record), ensure_ascii=False, allow_nan=False)
        )
    except (TypeError, ValueError) as error:
        raise ValueError("record must contain JSON-compatible values") from error

    for field in ("id", "source", "text"):
        value = normalized.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"record needs a non-empty string field: {field}")

    has_start = "word_start" in normalized
    has_end = "word_end" in normalized
    if has_start != has_end:
        raise ValueError("word_start and word_end must be provided together")
    if has_start:
        start = normalized["word_start"]
        end = normalized["word_end"]
        if (
            isinstance(start, bool)
            or isinstance(end, bool)
            or not isinstance(start, int)
            or not isinstance(end, int)
            or start < 0
            or end < start
        ):
            raise ValueError("word positions must be integers with 0 <= start <= end")
    return normalized


def _validate_query_params(k: int, min_score: float) -> None:
    if isinstance(k, bool) or not isinstance(k, int) or k <= 0:
        raise ValueError("k must be a positive integer")
    if (
        isinstance(min_score, bool)
        or not isinstance(min_score, Real)
        or not 0 <= min_score <= 1
    ):
        raise ValueError("min_score must be a number between 0 and 1")


class VectorStore:
    """Store traceable records and compatible vectors with exact search."""

    def __init__(self, *, embedding_id: str, dimension: int):
        if not isinstance(embedding_id, str) or not embedding_id.strip():
            raise ValueError("embedding_id must be a non-empty string")
        _validate_dimension(dimension)
        self.embedding_id = embedding_id
        self.dimension = dimension
        self.items: list[dict[str, Any]] = []
        self._ids: set[str] = set()

    def __len__(self) -> int:
        return len(self.items)

    def add(self, record: Mapping[str, Any], vector: Sequence[float]) -> None:
        normalized_record = _normalize_record(record)
        record_id = normalized_record["id"]
        if record_id in self._ids:
            raise ValueError(f"duplicate record id: {record_id}")
        normalized_vector = _normalize_vector(vector, self.dimension)
        self.items.append(
            {"record": normalized_record, "vector": normalized_vector}
        )
        self._ids.add(record_id)

    def query(
        self,
        vector: Sequence[float],
        *,
        k: int = 3,
        min_score: float = 0.0,
    ) -> list[dict[str, Any]]:
        _validate_query_params(k, min_score)
        query_vector = _normalize_vector(vector, self.dimension)
        if not any(query_vector):
            return []

        scored = [
            (cosine(query_vector, item["vector"]), position)
            for position, item in enumerate(self.items)
        ]
        scored.sort(key=lambda pair: (-pair[0], pair[1]))

        hits = []
        for score, position in scored:
            if score <= 0 or score < min_score:
                continue
            hit = dict(self.items[position]["record"])
            hit["score"] = round(score, 4)
            hits.append(hit)
            if len(hits) == k:
                break
        return hits

    def to_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "embedding": {
                "id": self.embedding_id,
                "dimension": self.dimension,
            },
            "items": [
                {
                    "record": dict(item["record"]),
                    "vector": list(item["vector"]),
                }
                for item in self.items
            ],
        }

    def save(self, path: str | Path) -> None:
        with Path(path).open("w", encoding="utf-8") as file:
            json.dump(
                self.to_manifest(),
                file,
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            )

    @classmethod
    def load(
        cls,
        path: str | Path,
        *,
        embedding_id: str,
        dimension: int,
    ) -> "VectorStore":
        with Path(path).open(encoding="utf-8") as file:
            manifest = json.load(file)

        if not isinstance(manifest, Mapping):
            raise ValueError("store manifest must be an object")
        if manifest.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(
                f"unsupported schema_version: {manifest.get('schema_version')!r}"
            )

        embedding = manifest.get("embedding")
        if not isinstance(embedding, Mapping):
            raise ValueError("store manifest needs embedding metadata")
        if embedding.get("id") != embedding_id:
            raise ValueError(
                "embedding id mismatch: "
                f"stored={embedding.get('id')!r}, expected={embedding_id!r}"
            )
        if embedding.get("dimension") != dimension:
            raise ValueError(
                "embedding dimension mismatch: "
                f"stored={embedding.get('dimension')!r}, expected={dimension!r}"
            )

        items = manifest.get("items")
        if not isinstance(items, list):
            raise ValueError("store manifest needs an items list")

        store = cls(embedding_id=embedding_id, dimension=dimension)
        for position, item in enumerate(items):
            if not isinstance(item, Mapping):
                raise ValueError(f"item at position {position} must be an object")
            if "record" not in item or "vector" not in item:
                raise ValueError(
                    f"item at position {position} needs record and vector"
                )
            store.add(item["record"], item["vector"])
        return store
