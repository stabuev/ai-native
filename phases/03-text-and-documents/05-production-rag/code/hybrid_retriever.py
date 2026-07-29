"""Rank fusion and comparative retrieval evaluation for lesson 3.5.

The module deliberately receives already ranked candidate IDs.  Producing
lexical or dense candidates is a separate retriever responsibility.  Keeping
that boundary visible lets the offline exercise focus on three production
properties:

    positive candidate lists -> RRF -> traceable records
    no candidates             -> []
    lexical vs dense vs hybrid -> one shared evaluation set
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any


def _positive_integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _normalize_rankings(
    rankings: Mapping[str, Sequence[str]],
) -> dict[str, list[str]]:
    if not isinstance(rankings, Mapping) or not rankings:
        raise ValueError("rankings must be a non-empty mapping")

    normalized: dict[str, list[str]] = {}
    for signal, ranking in rankings.items():
        if not isinstance(signal, str) or not signal.strip():
            raise ValueError("ranking names must be non-empty strings")
        if isinstance(ranking, (str, bytes)) or not isinstance(ranking, Sequence):
            raise TypeError(f"ranking {signal!r} must be a sequence of record IDs")

        ids = list(ranking)
        if any(not isinstance(record_id, str) or not record_id.strip() for record_id in ids):
            raise ValueError(f"ranking {signal!r} contains an invalid record ID")
        if len(ids) != len(set(ids)):
            raise ValueError(f"ranking {signal!r} contains duplicate record IDs")
        normalized[signal] = ids
    return normalized


def _record_map(
    records: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    if (
        isinstance(records, (str, bytes, Mapping))
        or not isinstance(records, Iterable)
    ):
        raise TypeError("records must be an iterable of traceable records")

    by_id: dict[str, dict[str, Any]] = {}
    for position, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise TypeError(f"record at position {position} must be a mapping")
        copy = dict(record)
        for field in ("id", "source", "text"):
            value = copy.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"record at position {position} needs a non-empty {field}"
                )
        record_id = copy["id"]
        if record_id in by_id:
            raise ValueError(f"duplicate record id: {record_id}")
        by_id[record_id] = copy
    return by_id


def reciprocal_rank_fusion(
    rankings: Mapping[str, Sequence[str]],
    *,
    rank_constant: int = 60,
) -> list[dict[str, Any]]:
    """Fuse ranked ID lists without comparing their raw scores.

    Every occurrence contributes ``1 / (rank_constant + rank)`` where ``rank``
    starts at one.  Ties retain the order in which an ID was first encountered:
    signal order first, position inside a signal second.
    """
    _positive_integer(rank_constant, "rank_constant")
    normalized = _normalize_rankings(rankings)

    scores: dict[str, float] = {}
    first_seen: dict[str, int] = {}
    ranks: dict[str, dict[str, int]] = {}

    for signal, ranking in normalized.items():
        for rank, record_id in enumerate(ranking, start=1):
            if record_id not in first_seen:
                first_seen[record_id] = len(first_seen)
            scores[record_id] = scores.get(record_id, 0.0) + (
                1.0 / (rank_constant + rank)
            )
            ranks.setdefault(record_id, {})[signal] = rank

    ordered_ids = sorted(
        scores,
        key=lambda record_id: (-scores[record_id], first_seen[record_id]),
    )
    return [
        {
            "id": record_id,
            "rrf_score": round(scores[record_id], 6),
            "matched_by": list(ranks[record_id]),
            "ranks": dict(ranks[record_id]),
        }
        for record_id in ordered_ids
    ]


def hybrid_search(
    rankings: Mapping[str, Sequence[str]],
    records: Iterable[Mapping[str, Any]],
    *,
    top_k: int = 3,
    rank_constant: int = 60,
) -> list[dict[str, Any]]:
    """Return fused candidates together with their canonical records.

    Candidate lists must contain only positive evidence produced by their
    retrievers.  If every list is empty, RRF has nothing to promote and the
    function returns ``[]``.
    """
    _positive_integer(top_k, "top_k")
    normalized = _normalize_rankings(rankings)
    if len(normalized) < 2:
        raise ValueError("hybrid search needs at least two rankings")

    records_by_id = _record_map(records)
    fused = reciprocal_rank_fusion(
        normalized,
        rank_constant=rank_constant,
    )

    unknown_ids = [item["id"] for item in fused if item["id"] not in records_by_id]
    if unknown_ids:
        raise ValueError(f"rankings contain unknown record id: {unknown_ids[0]}")

    hits = []
    for item in fused[:top_k]:
        hits.append(
            {
                "record": dict(records_by_id[item["id"]]),
                "rrf_score": item["rrf_score"],
                "matched_by": list(item["matched_by"]),
                "ranks": dict(item["ranks"]),
            }
        )
    return hits


def _new_stats() -> dict[str, int]:
    return {
        "total": 0,
        "passed": 0,
        "answerable_total": 0,
        "answerable_hits": 0,
        "no_answer_total": 0,
        "correct_abstentions": 0,
    }


def _finish_stats(stats: Mapping[str, int]) -> dict[str, Any]:
    total = stats["total"]
    answerable_total = stats["answerable_total"]
    no_answer_total = stats["no_answer_total"]
    return {
        "total": total,
        "passed": stats["passed"],
        "accuracy": round(stats["passed"] / total, 3) if total else 0.0,
        "answerable": {
            "total": answerable_total,
            "hits": stats["answerable_hits"],
            "hit_rate_at_k": (
                round(stats["answerable_hits"] / answerable_total, 3)
                if answerable_total
                else 0.0
            ),
        },
        "no_answer": {
            "total": no_answer_total,
            "correct_abstentions": stats["correct_abstentions"],
            "accuracy": (
                round(stats["correct_abstentions"] / no_answer_total, 3)
                if no_answer_total
                else 0.0
            ),
        },
    }


def evaluate(
    cases: Iterable[Mapping[str, Any]],
    records: Iterable[Mapping[str, Any]],
    *,
    top_k: int = 1,
    rank_constant: int = 60,
) -> dict[str, Any]:
    """Compare every retriever and their hybrid on exactly the same cases."""
    _positive_integer(top_k, "top_k")
    _positive_integer(rank_constant, "rank_constant")
    records_by_id = _record_map(records)

    if (
        isinstance(cases, (str, bytes, Mapping))
        or not isinstance(cases, Iterable)
    ):
        raise TypeError("cases must be an iterable of evaluation cases")
    case_list = list(cases)
    if not case_list:
        raise ValueError("evaluation needs at least one case")

    signal_order: tuple[str, ...] | None = None
    raw_stats: dict[str, dict[str, int]] = {}
    details = []

    for position, case in enumerate(case_list):
        if not isinstance(case, Mapping):
            raise TypeError(f"case at position {position} must be a mapping")

        case_id = case.get("id")
        query = case.get("query")
        expected_ids = case.get("expected_ids")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"case at position {position} needs a non-empty id")
        if not isinstance(query, str) or not query.strip():
            raise ValueError(f"case {case_id!r} needs a non-empty query")
        if (
            isinstance(expected_ids, (str, bytes))
            or not isinstance(expected_ids, Sequence)
            or any(
                not isinstance(record_id, str) or not record_id.strip()
                for record_id in expected_ids
            )
        ):
            raise ValueError(f"case {case_id!r} needs expected_ids as a list of IDs")
        if len(expected_ids) != len(set(expected_ids)):
            raise ValueError(f"case {case_id!r} contains duplicate expected IDs")
        unknown_expected = [
            record_id for record_id in expected_ids if record_id not in records_by_id
        ]
        if unknown_expected:
            raise ValueError(
                f"case {case_id!r} expects unknown record id: {unknown_expected[0]}"
            )

        normalized = _normalize_rankings(case.get("rankings"))
        current_order = tuple(normalized)
        if len(current_order) < 2:
            raise ValueError(f"case {case_id!r} needs at least two rankings")
        if signal_order is None:
            signal_order = current_order
            raw_stats = {
                variant: _new_stats()
                for variant in (*signal_order, "hybrid")
            }
        elif current_order != signal_order:
            raise ValueError(
                "all cases must use the same ranking names in the same order"
            )

        hybrid_hits = hybrid_search(
            normalized,
            records_by_id.values(),
            top_k=top_k,
            rank_constant=rank_constant,
        )
        retrieved = {
            signal: ranking[:top_k]
            for signal, ranking in normalized.items()
        }
        retrieved["hybrid"] = [
            hit["record"]["id"]
            for hit in hybrid_hits
        ]

        expected = set(expected_ids)
        passed_by_variant: dict[str, bool] = {}
        for variant, retrieved_ids in retrieved.items():
            stats = raw_stats[variant]
            stats["total"] += 1
            if expected:
                passed = bool(expected & set(retrieved_ids))
                stats["answerable_total"] += 1
                stats["answerable_hits"] += int(passed)
            else:
                passed = not retrieved_ids
                stats["no_answer_total"] += 1
                stats["correct_abstentions"] += int(passed)
            stats["passed"] += int(passed)
            passed_by_variant[variant] = passed

        details.append(
            {
                "id": case_id,
                "query": query,
                "expected_ids": list(expected_ids),
                "retrieved_ids": retrieved,
                "passed": passed_by_variant,
            }
        )

    return {
        "top_k": top_k,
        "rank_constant": rank_constant,
        "variants": {
            variant: _finish_stats(stats)
            for variant, stats in raw_stats.items()
        },
        "cases": details,
    }


if __name__ == "__main__":
    from sample_rankings import EVAL_CASES, SAMPLE_RECORDS

    for demo_top_k in (1, 2):
        report = evaluate(
            EVAL_CASES,
            SAMPLE_RECORDS,
            top_k=demo_top_k,
        )
        summary = {
            variant: data["passed"]
            for variant, data in report["variants"].items()
        }
        print(f"\ntop_k={demo_top_k}: {json.dumps(summary, ensure_ascii=False)}")
        for case in report["cases"]:
            print(
                f"  {case['id']}: "
                f"{json.dumps(case['retrieved_ids'], ensure_ascii=False)}"
            )
