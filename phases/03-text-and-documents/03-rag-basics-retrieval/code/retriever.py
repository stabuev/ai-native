"""Traceable lexical retrieval for lesson 3.3.

The implementation is deliberately small and offline.  It keeps the provenance
records produced in lesson 3.2, ranks them with TF-IDF and cosine similarity,
abstains when there is no lexical evidence, and evaluates retrieval separately
from answer generation.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from numbers import Real
from typing import Any


# A short, inspectable list is enough for the exercise.  It prevents a query
# such as "и в на" from becoming evidence.  It is not a universal language
# model or a production Russian stop-word list.
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

REQUIRED_CHUNK_FIELDS = ("id", "source", "text")


def _tokens(text: str) -> list[str]:
    """Return lowercase word tokens without the exercise stop words."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return [
        token
        for token in re.findall(r"\w+", text.lower())
        if token not in STOP_WORDS
    ]


def _tfidf(tokens: Sequence[str], idf: Mapping[str, float]) -> dict[str, float]:
    """Build a sparse TF-IDF vector represented as ``{term: weight}``."""
    counts = Counter(tokens)
    total = sum(counts.values())
    if total == 0:
        return {}
    return {
        term: (count / total) * idf.get(term, 0.0)
        for term, count in counts.items()
        if term in idf
    }


def _validated_chunk(chunk: Any, position: int) -> dict[str, Any]:
    if not isinstance(chunk, Mapping):
        raise TypeError(f"chunk at position {position} must be a mapping")

    record = dict(chunk)
    missing = [field for field in REQUIRED_CHUNK_FIELDS if field not in record]
    if missing:
        raise ValueError(
            f"chunk at position {position} is missing fields: {', '.join(missing)}"
        )
    for field in REQUIRED_CHUNK_FIELDS:
        if not isinstance(record[field], str) or not record[field].strip():
            raise ValueError(
                f"chunk at position {position} has invalid {field!r}"
            )
    return record


def build_index(chunks: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Build an in-memory TF-IDF index and preserve every chunk field."""
    if isinstance(chunks, (str, bytes)) or not isinstance(chunks, Iterable):
        raise TypeError("chunks must be an iterable of traceable records")

    records = [
        _validated_chunk(chunk, position)
        for position, chunk in enumerate(chunks)
    ]
    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("chunk ids must be unique")

    tokenized = [_tokens(record["text"]) for record in records]
    document_frequency: Counter[str] = Counter()
    for tokens in tokenized:
        document_frequency.update(set(tokens))

    count = len(records)
    idf = {
        term: math.log((count + 1) / (frequency + 1)) + 1
        for term, frequency in document_frequency.items()
    }
    return {
        "chunks": records,
        "idf": idf,
        "vectors": [_tfidf(tokens, idf) for tokens in tokenized],
    }


def _cosine(a: Mapping[str, float], b: Mapping[str, float]) -> float:
    """Return cosine similarity for two sparse vectors."""
    common = set(a) & set(b)
    dot = sum(a[term] * b[term] for term in common)
    norm_a = math.sqrt(sum(value * value for value in a.values()))
    norm_b = math.sqrt(sum(value * value for value in b.values()))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def _validate_search_params(k: int, min_score: float) -> None:
    if isinstance(k, bool) or not isinstance(k, int) or k <= 0:
        raise ValueError("k must be a positive integer")
    if (
        isinstance(min_score, bool)
        or not isinstance(min_score, Real)
        or not 0 <= min_score <= 1
    ):
        raise ValueError("min_score must be a number between 0 and 1")


def search(
    query: str,
    index: Mapping[str, Any],
    k: int = 3,
    min_score: float = 0.0,
) -> list[dict[str, Any]]:
    """Return at most ``k`` positive lexical matches with provenance.

    ``min_score=0`` means "accept any positive lexical evidence", not "return
    zero-score chunks".  A higher threshold must be selected against an
    evaluation set for the actual corpus.
    """
    if not isinstance(query, str):
        raise TypeError("query must be a string")
    _validate_search_params(k, min_score)

    query_vector = _tfidf(_tokens(query), index["idf"])
    if not query_vector:
        return []

    scored = [
        (_cosine(query_vector, vector), position)
        for position, vector in enumerate(index["vectors"])
    ]
    # The original chunk order is the explicit tie-breaker.
    scored.sort(key=lambda item: (-item[0], item[1]))

    hits = []
    for score, position in scored:
        if score <= 0 or score < min_score:
            continue
        hit = dict(index["chunks"][position])
        hit["score"] = round(score, 4)
        hits.append(hit)
        if len(hits) == k:
            break
    return hits


def evaluate(
    cases: Iterable[Mapping[str, Any]],
    index: Mapping[str, Any],
    k: int = 3,
    min_score: float = 0.0,
) -> dict[str, Any]:
    """Evaluate expected IDs and expected abstentions on a small query set."""
    _validate_search_params(k, min_score)

    details = []
    answerable_total = 0
    answerable_hits = 0
    no_answer_total = 0
    correct_abstentions = 0

    for position, case in enumerate(cases):
        if not isinstance(case, Mapping):
            raise TypeError(f"case at position {position} must be a mapping")
        query = case.get("query")
        expected_ids = case.get("expected_ids")
        if not isinstance(query, str) or not query.strip():
            raise ValueError(f"case at position {position} needs a non-empty query")
        if (
            isinstance(expected_ids, (str, bytes))
            or not isinstance(expected_ids, Sequence)
            or any(not isinstance(item, str) for item in expected_ids)
        ):
            raise ValueError(
                f"case at position {position} needs expected_ids as a list of strings"
            )

        expected = set(expected_ids)
        hits = search(query, index, k=k, min_score=min_score)
        retrieved_ids = [hit["id"] for hit in hits]
        if expected:
            answerable_total += 1
            passed = bool(expected & set(retrieved_ids))
            answerable_hits += int(passed)
        else:
            no_answer_total += 1
            passed = not retrieved_ids
            correct_abstentions += int(passed)

        details.append(
            {
                "query": query,
                "expected_ids": list(expected_ids),
                "retrieved_ids": retrieved_ids,
                "passed": passed,
            }
        )

    total = len(details)
    passed_total = answerable_hits + correct_abstentions
    return {
        "k": k,
        "min_score": min_score,
        "total": total,
        "passed": passed_total,
        "accuracy": round(passed_total / total, 3) if total else 0.0,
        "answerable": {
            "total": answerable_total,
            "hits": answerable_hits,
            "hit_rate_at_k": (
                round(answerable_hits / answerable_total, 3)
                if answerable_total
                else 0.0
            ),
        },
        "no_answer": {
            "total": no_answer_total,
            "correct_abstentions": correct_abstentions,
            "accuracy": (
                round(correct_abstentions / no_answer_total, 3)
                if no_answer_total
                else 0.0
            ),
        },
        "cases": details,
    }


if __name__ == "__main__":
    from sample_chunks import EVAL_CASES, SAMPLE_CHUNKS

    demo_index = build_index(SAMPLE_CHUNKS)
    for demo_query in [
        "согласование получено 16 сентября запуск переносится",
        "какой рекламный бюджет",
        "кто автор финального документа",
    ]:
        print(f"\nЗапрос: {demo_query}")
        found = search(demo_query, demo_index, k=2)
        if not found:
            print("  доказательств не найдено")
        for result in found:
            print(f"  {result['score']:.3f}  {result['id']}  {result['text']}")

    print("\nEvaluation:")
    print(evaluate(EVAL_CASES, demo_index, k=2))
