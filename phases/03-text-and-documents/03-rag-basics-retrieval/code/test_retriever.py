import sys
from pathlib import Path

import pytest

from retriever import _tokens, build_index, evaluate, search
from sample_chunks import EVAL_CASES, SAMPLE_CHUNKS

try:
    from mini_rag import answer_with, prepare_request
except ModuleNotFoundError:
    outputs_dir = Path(__file__).resolve().parents[1] / "outputs"
    sys.path.insert(0, str(outputs_dir))
    from mini_rag import answer_with, prepare_request


def test_tokenization_removes_stop_words_and_rejects_non_text():
    assert _tokens("И В запуск, ЗАПУСК!") == ["запуск", "запуск"]
    with pytest.raises(TypeError, match="string"):
        _tokens(None)


def test_relevant_chunk_is_ranked_first_and_keeps_provenance():
    index = build_index(SAMPLE_CHUNKS)

    hits = search(
        "согласование получено 16 сентября запуск переносится",
        index,
        k=2,
    )

    assert hits[0]["id"] == "sample_report.md#chunk-0002"
    assert hits[0]["source"] == "sample_report.md"
    assert hits[0]["word_start"] == 120
    assert hits[0]["word_end"] == 190
    assert 0 < hits[0]["score"] <= 1


def test_top_k_limits_only_positive_matches():
    index = build_index(SAMPLE_CHUNKS)

    hits = search("пилот метрики", index, k=2)

    assert 0 < len(hits) <= 2
    assert all(hit["score"] > 0 for hit in hits)


@pytest.mark.parametrize(
    "query",
    [
        "",
        "   ",
        "и в на",
        "квантовая криптография блокчейн",
    ],
)
def test_query_without_lexical_evidence_returns_no_chunks(query):
    index = build_index(SAMPLE_CHUNKS)

    assert search(query, index, k=3) == []


def test_min_score_can_reject_a_weak_match_without_hiding_zeroes_in_top_k():
    index = build_index(SAMPLE_CHUNKS)
    weak_hits = search("сентября", index, k=7, min_score=0.0)

    assert weak_hits
    assert search("сентября", index, k=7, min_score=0.9) == []


@pytest.mark.parametrize("invalid_k", [0, -1, 1.5, True])
def test_invalid_k_is_rejected(invalid_k):
    index = build_index(SAMPLE_CHUNKS)

    with pytest.raises(ValueError, match="positive integer"):
        search("пилот", index, k=invalid_k)


@pytest.mark.parametrize("invalid_score", [-0.1, 1.1, "0.2", True])
def test_invalid_min_score_is_rejected(invalid_score):
    index = build_index(SAMPLE_CHUNKS)

    with pytest.raises(ValueError, match="between 0 and 1"):
        search("пилот", index, min_score=invalid_score)


def test_duplicate_chunk_ids_are_rejected_before_provenance_becomes_ambiguous():
    duplicate = [SAMPLE_CHUNKS[0], dict(SAMPLE_CHUNKS[0])]

    with pytest.raises(ValueError, match="unique"):
        build_index(duplicate)


@pytest.mark.parametrize(
    "invalid_chunks, message",
    [
        ("plain text", "iterable of traceable records"),
        ([{"id": "a", "text": "content"}], "missing fields"),
        ([{"id": "a", "source": "demo", "text": "  "}], "invalid 'text'"),
    ],
)
def test_invalid_chunk_contract_is_rejected(invalid_chunks, message):
    with pytest.raises((TypeError, ValueError), match=message):
        build_index(invalid_chunks)


def test_original_order_is_the_stable_tie_breaker():
    chunks = [
        {"id": "a", "source": "demo", "text": "общий термин"},
        {"id": "b", "source": "demo", "text": "общий термин"},
    ]

    assert [hit["id"] for hit in search("термин", build_index(chunks))] == [
        "a",
        "b",
    ]


def test_evaluation_separates_answerable_hits_from_correct_abstention():
    report = evaluate(EVAL_CASES, build_index(SAMPLE_CHUNKS), k=2)

    assert report["total"] == 5
    assert report["answerable"]["total"] == 4
    assert report["answerable"]["hits"] == 3
    assert report["answerable"]["hit_rate_at_k"] == 0.75
    assert report["no_answer"] == {
        "total": 1,
        "correct_abstentions": 1,
        "accuracy": 1.0,
    }
    lexical_miss = report["cases"][-1]
    assert lexical_miss["passed"] is False
    assert lexical_miss["retrieved_ids"] == []


def test_mini_rag_prompt_keeps_evidence_ids_and_sources():
    request = prepare_request(
        "когда запускается пилот iOS",
        build_index(SAMPLE_CHUNKS),
        k=1,
    )

    assert request["status"] == "evidence_found"
    assert request["evidence"][0]["id"] in request["prompt"]
    assert request["evidence"][0]["source"] in request["prompt"]


def test_mini_rag_does_not_call_generator_without_evidence():
    calls = []

    def generate(prompt):
        calls.append(prompt)
        return "unexpected"

    result = answer_with(
        "какой рекламный бюджет",
        build_index(SAMPLE_CHUNKS),
        generate,
    )

    assert calls == []
    assert result["status"] == "insufficient_context"
    assert result["prompt"] is None
    assert result["generator_called"] is False
