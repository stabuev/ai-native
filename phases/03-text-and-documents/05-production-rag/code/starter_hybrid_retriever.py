"""Starter for the offline Build It exercise from lesson 3.5.

Copy this file as ``hybrid_retriever.py``.  Candidate generation is already
represented by frozen ranked IDs in ``sample_rankings.py``; implement fusion,
traceable search and comparative evaluation.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any


def reciprocal_rank_fusion(
    rankings: Mapping[str, Sequence[str]],
    *,
    rank_constant: int = 60,
) -> list[dict[str, Any]]:
    """Fuse unique ranked IDs and expose score, signals and one-based ranks."""
    raise NotImplementedError


def hybrid_search(
    rankings: Mapping[str, Sequence[str]],
    records: Iterable[Mapping[str, Any]],
    *,
    top_k: int = 3,
    rank_constant: int = 60,
) -> list[dict[str, Any]]:
    """Return top-k fused candidates together with canonical records."""
    raise NotImplementedError


def evaluate(
    cases: Iterable[Mapping[str, Any]],
    records: Iterable[Mapping[str, Any]],
    *,
    top_k: int = 1,
    rank_constant: int = 60,
) -> dict[str, Any]:
    """Compare each signal and their hybrid on the same evaluation cases."""
    raise NotImplementedError


if __name__ == "__main__":
    from sample_rankings import EVAL_CASES, SAMPLE_RECORDS

    print(evaluate(EVAL_CASES, SAMPLE_RECORDS, top_k=1))
