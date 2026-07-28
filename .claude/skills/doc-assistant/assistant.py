"""Runnable baseline document assistant for lesson 3.4.

The script indexes traceable JSON records, persists them, and prepares a
grounded request.  It intentionally does not call a model: an empty retrieval
must stop the chain before generation.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from vector_store import (
    HASH_DIMENSION,
    HASH_EMBEDDING_ID,
    VectorStore,
    hash_embed,
)


def _read_records(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as file:
        records = json.load(file)
    if (
        isinstance(records, (str, bytes))
        or not isinstance(records, Sequence)
        or any(not isinstance(record, Mapping) for record in records)
    ):
        raise ValueError("records file must contain a JSON array of objects")
    return [dict(record) for record in records]


def new_store() -> VectorStore:
    return VectorStore(
        embedding_id=HASH_EMBEDDING_ID,
        dimension=HASH_DIMENSION,
    )


def load_store(path: str | Path) -> VectorStore:
    return VectorStore.load(
        path,
        embedding_id=HASH_EMBEDDING_ID,
        dimension=HASH_DIMENSION,
    )


def add_records(
    store: VectorStore,
    records: Sequence[Mapping[str, Any]],
) -> VectorStore:
    for record in records:
        text = record.get("text")
        if not isinstance(text, str):
            raise ValueError("every record needs a string text field")
        store.add(record, hash_embed(text))
    return store


def index_records(
    records: Sequence[Mapping[str, Any]],
    path: str | Path,
) -> VectorStore:
    store = add_records(new_store(), records)
    store.save(path)
    return store


def append_records(
    records: Sequence[Mapping[str, Any]],
    path: str | Path,
) -> VectorStore:
    store = add_records(load_store(path), records)
    store.save(path)
    return store


def _location(hit: Mapping[str, Any]) -> str:
    start = hit.get("word_start")
    end = hit.get("word_end")
    if isinstance(start, int) and isinstance(end, int):
        return f"слова {start}:{end}"
    return "позиция не указана"


def build_prompt(query: str, evidence: list[dict[str, Any]]) -> str:
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
        "Ответь на вопрос только по фрагментам ниже. После каждого проверяемого "
        "утверждения укажи ID фрагмента в квадратных скобках. Если фрагменты "
        "тематически близки, но не содержат ответа, скажи: "
        "«Недостаточно контекста для ответа».\n\n"
        f"Фрагменты:\n{context}\n\n"
        f"Вопрос: {query}\n"
        "Ответ:"
    )


def prepare_request(
    query: str,
    store: VectorStore,
    *,
    k: int = 3,
    min_score: float = 0.0,
) -> dict[str, Any]:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")

    evidence = store.query(hash_embed(query), k=k, min_score=min_score)
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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    index = commands.add_parser("index", help="create a new store")
    index.add_argument("records")
    index.add_argument("store")

    add = commands.add_parser("add", help="append unique records")
    add.add_argument("records")
    add.add_argument("store")

    ask = commands.add_parser("ask", help="retrieve evidence for a question")
    ask.add_argument("store")
    ask.add_argument("query")
    ask.add_argument("--k", type=int, default=3)
    ask.add_argument("--min-score", type=float, default=0.0)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "index":
        store = index_records(_read_records(args.records), args.store)
        result = {"status": "indexed", "records": len(store), "store": args.store}
    elif args.command == "add":
        store = append_records(_read_records(args.records), args.store)
        result = {"status": "updated", "records": len(store), "store": args.store}
    else:
        result = prepare_request(
            args.query,
            load_store(args.store),
            k=args.k,
            min_score=args.min_score,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
