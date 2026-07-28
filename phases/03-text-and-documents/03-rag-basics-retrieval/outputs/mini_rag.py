"""Mini-RAG artifact for lesson 3.3.

Copy this file next to the completed ``retriever.py``.  The artifact does not
duplicate retrieval logic: it turns traceable hits into an evidence package and
stops before generation when the retriever found no lexical evidence.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any


# In the repository the solution lives in ../code.  After a learner copies both
# files into course-work/3.3, the normal import succeeds without this fallback.
try:
    from retriever import build_index, search
except ModuleNotFoundError:
    code_dir = Path(__file__).resolve().parents[1] / "code"
    sys.path.insert(0, str(code_dir))
    from retriever import build_index, search


def _location(hit: Mapping[str, Any]) -> str:
    start = hit.get("word_start")
    end = hit.get("word_end")
    if isinstance(start, int) and isinstance(end, int):
        return f"слова {start}:{end}"
    return "позиция не указана"


def build_prompt(query: str, evidence: list[dict[str, Any]]) -> str:
    """Build a grounded prompt from non-empty traceable evidence."""
    if not evidence:
        raise ValueError("evidence must be non-empty")

    blocks = []
    for hit in evidence:
        blocks.append(
            f"[{hit['id']}]\n"
            f"Источник: {hit['source']}, {_location(hit)}, score={hit['score']}\n"
            f"Текст: {hit['text']}"
        )
    context = "\n\n".join(blocks)
    return (
        "Ответь на вопрос только по фрагментам ниже. "
        "После каждого проверяемого утверждения укажи ID фрагмента в квадратных "
        "скобках. Если найденные фрагменты не содержат ответа, прямо скажи: "
        "«Недостаточно контекста для ответа».\n\n"
        f"Фрагменты:\n{context}\n\n"
        f"Вопрос: {query}\n"
        "Ответ:"
    )


def prepare_request(
    query: str,
    index: Mapping[str, Any],
    k: int = 3,
    min_score: float = 0.0,
) -> dict[str, Any]:
    """Retrieve evidence and prepare a request without calling a model."""
    evidence = search(query, index, k=k, min_score=min_score)
    if not evidence:
        return {
            "status": "insufficient_context",
            "query": query,
            "evidence": [],
            "prompt": None,
        }
    return {
        "status": "evidence_found",
        "query": query,
        "evidence": evidence,
        "prompt": build_prompt(query, evidence),
    }


def answer_with(
    query: str,
    index: Mapping[str, Any],
    generate: Callable[[str], str],
    k: int = 3,
    min_score: float = 0.0,
) -> dict[str, Any]:
    """Call ``generate`` only when retrieval produced positive evidence."""
    if not callable(generate):
        raise TypeError("generate must be callable")

    request = prepare_request(query, index, k=k, min_score=min_score)
    if request["status"] == "insufficient_context":
        return {
            **request,
            "answer": "Недостаточно контекста для ответа.",
            "generator_called": False,
        }

    answer = generate(request["prompt"])
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("generate must return a non-empty string")
    return {
        **request,
        "answer": answer,
        "generator_called": True,
    }


if __name__ == "__main__":
    from sample_chunks import SAMPLE_CHUNKS

    demo_index = build_index(SAMPLE_CHUNKS)
    for demo_query in [
        "когда запускается пилот iOS",
        "какой рекламный бюджет",
    ]:
        request = prepare_request(demo_query, demo_index, k=2)
        print(f"\n{demo_query}\nstatus={request['status']}")
        if request["prompt"]:
            print(request["prompt"])
