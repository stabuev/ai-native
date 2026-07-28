"""Starter for the offline Build It exercise from lesson 3.3.

Copy this file as ``retriever.py`` and implement the marked functions.
Use only the Python standard library.
"""

from __future__ import annotations

import math
import re
from collections import Counter


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


def _tokens(text):
    """Return lowercase word tokens without STOP_WORDS."""
    raise NotImplementedError


def _tfidf(tokens, idf):
    """Return a sparse ``{term: tf * idf}`` vector."""
    raise NotImplementedError


def _cosine(a, b):
    """Return cosine similarity for two sparse vectors."""
    raise NotImplementedError


def build_index(chunks):
    """Validate traceable chunks and preserve them in a TF-IDF index.

    Every chunk needs non-empty ``id``, ``source`` and ``text`` fields.
    IDs must be unique.  Preserve all additional metadata.
    """
    raise NotImplementedError


def search(query, index, k=3, min_score=0.0):
    """Return up to k positive matches with metadata and rounded score.

    Reject invalid ``k`` and ``min_score``.  Empty, stop-word-only and
    out-of-vocabulary queries return ``[]``.
    """
    raise NotImplementedError


def evaluate(cases, index, k=3, min_score=0.0):
    """Report Hit@k for answerable cases and accuracy for expected abstentions."""
    raise NotImplementedError


if __name__ == "__main__":
    from sample_chunks import EVAL_CASES, SAMPLE_CHUNKS

    index = build_index(SAMPLE_CHUNKS)
    print(search("согласование получено 16 сентября запуск переносится", index, k=2))
    print(evaluate(EVAL_CASES, index, k=2))
