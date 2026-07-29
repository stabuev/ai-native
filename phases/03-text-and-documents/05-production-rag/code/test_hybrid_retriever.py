import copy

import pytest

from hybrid_retriever import evaluate, hybrid_search, reciprocal_rank_fusion
from sample_rankings import (
    EVAL_CASES,
    IOS_LAUNCH,
    PILOT_METRICS,
    REPORT_OWNER,
    SAMPLE_RECORDS,
)


def case(case_id):
    return next(item for item in EVAL_CASES if item["id"] == case_id)


def test_rrf_uses_positions_and_exposes_its_trace():
    fused = reciprocal_rank_fusion(
        {
            "lexical": ["a", "b"],
            "dense": ["c", "a"],
        }
    )

    assert [item["id"] for item in fused] == ["a", "c", "b"]
    assert fused[0] == {
        "id": "a",
        "rrf_score": round(1 / 61 + 1 / 62, 6),
        "matched_by": ["lexical", "dense"],
        "ranks": {"lexical": 1, "dense": 2},
    }


def test_rrf_tie_break_is_stable_and_explicitly_depends_on_signal_order():
    lexical_first = reciprocal_rank_fusion(
        {"lexical": ["a"], "dense": ["b"]}
    )
    dense_first = reciprocal_rank_fusion(
        {"dense": ["b"], "lexical": ["a"]}
    )

    assert [item["id"] for item in lexical_first] == ["a", "b"]
    assert [item["id"] for item in dense_first] == ["b", "a"]


def test_empty_candidate_lists_do_not_create_evidence():
    assert reciprocal_rank_fusion({"lexical": [], "dense": []}) == []
    assert (
        hybrid_search(
            {"lexical": [], "dense": []},
            SAMPLE_RECORDS,
            top_k=3,
        )
        == []
    )


@pytest.mark.parametrize("rank_constant", [0, -1, True, 1.5])
def test_invalid_rank_constant_is_rejected(rank_constant):
    with pytest.raises(ValueError, match="rank_constant"):
        reciprocal_rank_fusion(
            {"lexical": ["a"]},
            rank_constant=rank_constant,
        )


def test_duplicate_id_inside_one_ranking_is_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        reciprocal_rank_fusion({"lexical": ["a", "a"]})


@pytest.mark.parametrize(
    "rankings",
    [
        {},
        {"": ["a"]},
        {"lexical": "a"},
        {"lexical": [""]},
    ],
)
def test_invalid_ranking_contract_is_rejected(rankings):
    with pytest.raises((TypeError, ValueError)):
        reciprocal_rank_fusion(rankings)


def test_hybrid_search_preserves_the_canonical_record_and_adds_fusion_trace():
    original_records = copy.deepcopy(SAMPLE_RECORDS)
    launch_case = case("exact-launch")
    for record in SAMPLE_RECORDS:
        assert len(record["text"].split()) == (
            record["word_end"] - record["word_start"]
        )

    hits = hybrid_search(
        launch_case["rankings"],
        SAMPLE_RECORDS,
        top_k=1,
    )

    assert hits[0]["record"]["id"] == IOS_LAUNCH
    assert hits[0]["record"]["source"] == "sample_report.md"
    assert hits[0]["record"]["word_start"] == 0
    assert hits[0]["matched_by"] == ["lexical", "dense"]
    assert hits[0]["ranks"] == {"lexical": 1, "dense": 2}
    assert SAMPLE_RECORDS == original_records


def test_hybrid_search_rejects_unknown_candidate_id():
    with pytest.raises(ValueError, match="unknown record id"):
        hybrid_search(
            {"lexical": ["missing"], "dense": []},
            SAMPLE_RECORDS,
        )


def test_hybrid_search_requires_two_signals():
    with pytest.raises(ValueError, match="at least two"):
        hybrid_search({"lexical": [IOS_LAUNCH]}, SAMPLE_RECORDS)


@pytest.mark.parametrize("top_k", [0, -1, True, 1.5])
def test_invalid_top_k_is_rejected(top_k):
    with pytest.raises(ValueError, match="top_k"):
        hybrid_search(
            {"lexical": [IOS_LAUNCH], "dense": []},
            SAMPLE_RECORDS,
            top_k=top_k,
        )


def test_top_one_evaluation_shows_gain_and_regression_instead_of_hiding_them():
    report = evaluate(EVAL_CASES, SAMPLE_RECORDS, top_k=1)

    assert {
        variant: result["passed"]
        for variant, result in report["variants"].items()
    } == {
        "lexical": 4,
        "dense": 4,
        "hybrid": 5,
    }
    details = {item["id"]: item for item in report["cases"]}
    assert details["exact-launch"]["passed"] == {
        "lexical": True,
        "dense": False,
        "hybrid": True,
    }
    assert details["support-role"]["passed"] == {
        "lexical": False,
        "dense": True,
        "hybrid": False,
    }


def test_top_two_hybrid_passes_all_sample_cases_but_baselines_do_not():
    report = evaluate(EVAL_CASES, SAMPLE_RECORDS, top_k=2)

    assert report["variants"]["lexical"]["passed"] == 4
    assert report["variants"]["dense"]["passed"] == 5
    assert report["variants"]["hybrid"]["passed"] == 6
    assert report["variants"]["hybrid"]["answerable"] == {
        "total": 5,
        "hits": 5,
        "hit_rate_at_k": 1.0,
    }
    assert report["variants"]["hybrid"]["no_answer"] == {
        "total": 1,
        "correct_abstentions": 1,
        "accuracy": 1.0,
    }


def test_no_answer_false_positive_fails_for_the_responsible_variants():
    false_positive_case = [
        {
            "id": "false-positive",
            "query": "вопрос вне корпуса",
            "expected_ids": [],
            "rankings": {
                "lexical": [PILOT_METRICS],
                "dense": [],
            },
        }
    ]

    report = evaluate(false_positive_case, SAMPLE_RECORDS, top_k=1)

    assert report["variants"]["lexical"]["no_answer"]["accuracy"] == 0.0
    assert report["variants"]["dense"]["no_answer"]["accuracy"] == 1.0
    assert report["variants"]["hybrid"]["no_answer"]["accuracy"] == 0.0


def test_evaluation_requires_consistent_signal_names_and_order():
    changed = copy.deepcopy(EVAL_CASES[:2])
    changed[1]["rankings"] = {
        "dense": [REPORT_OWNER],
        "lexical": [],
    }

    with pytest.raises(ValueError, match="same ranking names"):
        evaluate(changed, SAMPLE_RECORDS)


@pytest.mark.parametrize(
    "broken_case, message",
    [
        (
            {
                "id": "",
                "query": "q",
                "expected_ids": [],
                "rankings": {"lexical": [], "dense": []},
            },
            "non-empty id",
        ),
        (
            {
                "id": "x",
                "query": "",
                "expected_ids": [],
                "rankings": {"lexical": [], "dense": []},
            },
            "non-empty query",
        ),
        (
            {
                "id": "x",
                "query": "q",
                "expected_ids": ["missing"],
                "rankings": {"lexical": [], "dense": []},
            },
            "unknown record id",
        ),
    ],
)
def test_invalid_evaluation_case_is_rejected(broken_case, message):
    with pytest.raises(ValueError, match=message):
        evaluate([broken_case], SAMPLE_RECORDS)


def test_evaluation_needs_at_least_one_case():
    with pytest.raises(ValueError, match="at least one"):
        evaluate([], SAMPLE_RECORDS)
