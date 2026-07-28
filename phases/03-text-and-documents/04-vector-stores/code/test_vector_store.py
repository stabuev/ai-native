import json

import pytest

from sample_records import SAMPLE_RECORDS
from vector_store import (
    HASH_DIMENSION,
    HASH_EMBEDDING_ID,
    SCHEMA_VERSION,
    VectorStore,
    cosine,
    hash_embed,
)


def make_store(records=SAMPLE_RECORDS):
    store = VectorStore(
        embedding_id=HASH_EMBEDDING_ID,
        dimension=HASH_DIMENSION,
    )
    for record in records:
        store.add(record, hash_embed(record["text"]))
    return store


def test_hash_adapter_is_deterministic_fixed_size_and_lexical():
    first = hash_embed("согласование запуска")
    second = hash_embed("согласование запуска")

    assert len(first) == HASH_DIMENSION
    assert first == second
    assert hash_embed("и в на") == [0.0] * HASH_DIMENSION


def test_store_preserves_provenance_in_hits():
    hits = make_store().query(
        hash_embed("согласование получено 16 сентября запуск переносится"),
        k=1,
    )

    assert hits[0]["id"] == "sample_report.md#chunk-0002"
    assert hits[0]["source"] == "sample_report.md"
    assert hits[0]["word_start"] == 120
    assert hits[0]["word_end"] == 190
    assert 0 < hits[0]["score"] <= 1


def test_add_does_not_mutate_input_record():
    record = dict(SAMPLE_RECORDS[0])
    original = dict(record)

    make_store([]).add(record, hash_embed(record["text"]))

    assert record == original
    assert "score" not in record


def test_duplicate_id_is_rejected():
    store = make_store([SAMPLE_RECORDS[0]])

    with pytest.raises(ValueError, match="duplicate record id"):
        store.add(SAMPLE_RECORDS[0], hash_embed(SAMPLE_RECORDS[0]["text"]))
    assert len(store) == 1


@pytest.mark.parametrize(
    "record",
    [
        {"source": "report.md", "text": "text"},
        {"id": "x", "text": "text"},
        {"id": "x", "source": "report.md", "text": ""},
        {
            "id": "x",
            "source": "report.md",
            "text": "text",
            "word_start": 5,
            "word_end": 4,
        },
    ],
)
def test_invalid_traceable_record_is_rejected(record):
    with pytest.raises(ValueError):
        make_store([]).add(record, [0.0] * HASH_DIMENSION)


def test_vector_dimension_and_values_are_validated():
    store = make_store([])
    record = SAMPLE_RECORDS[0]

    with pytest.raises(ValueError, match="dimension"):
        store.add(record, [1.0])
    with pytest.raises(ValueError, match="finite"):
        store.add(record, [float("nan")] * HASH_DIMENSION)


def test_cosine_rejects_different_dimensions():
    with pytest.raises(ValueError, match="equal dimensions"):
        cosine([1.0], [1.0, 0.0])


def test_zero_vector_and_no_positive_match_return_empty_result():
    store = make_store()

    assert store.query([0.0] * HASH_DIMENSION) == []
    assert store.query(hash_embed("термоядерныйсинхрофазотрон"), k=3) == []
    assert store.query(hash_embed("какой рекламный бюджет"), k=3) == []
    # The record exists, but the lexical adapter misses this paraphrase.
    assert store.query(hash_embed("кто автор финального документа"), k=3) == []


@pytest.mark.parametrize("k", [0, -1, True, 1.5])
def test_invalid_k_is_rejected(k):
    with pytest.raises(ValueError, match="k must"):
        make_store().query(hash_embed("пилот"), k=k)


@pytest.mark.parametrize("min_score", [-0.1, 1.1, True, "0.2"])
def test_invalid_min_score_is_rejected(min_score):
    with pytest.raises(ValueError, match="min_score"):
        make_store().query(hash_embed("пилот"), min_score=min_score)


def test_min_score_filters_weak_matches():
    store = make_store()

    assert store.query(hash_embed("пилот"), k=4, min_score=1.0) == []


def test_save_load_preserves_manifest_and_ranked_results(tmp_path):
    store = make_store()
    query_vector = hash_embed(
        "согласование получено 16 сентября запуск переносится"
    )
    expected_hits = store.query(query_vector, k=2)
    path = tmp_path / "store.json"

    store.save(path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    restored = VectorStore.load(
        path,
        embedding_id=HASH_EMBEDDING_ID,
        dimension=HASH_DIMENSION,
    )

    assert manifest["schema_version"] == SCHEMA_VERSION
    assert manifest["embedding"] == {
        "id": HASH_EMBEDDING_ID,
        "dimension": HASH_DIMENSION,
    }
    assert restored.query(query_vector, k=2) == expected_hits
    assert restored.to_manifest() == store.to_manifest()


def test_loaded_store_accepts_new_unique_record_without_rebuilding_old_ones(tmp_path):
    store = make_store(SAMPLE_RECORDS[:2])
    original_vectors = [
        list(item["vector"])
        for item in store.items
    ]
    path = tmp_path / "store.json"
    store.save(path)

    restored = VectorStore.load(
        path,
        embedding_id=HASH_EMBEDDING_ID,
        dimension=HASH_DIMENSION,
    )
    restored.add(
        SAMPLE_RECORDS[2],
        hash_embed(SAMPLE_RECORDS[2]["text"]),
    )

    assert len(restored) == 3
    assert [item["vector"] for item in restored.items[:2]] == original_vectors
    assert (
        restored.query(hash_embed("метрики успешных оплат"), k=1)[0]["id"]
        == "sample_report.md#chunk-0004"
    )


def test_load_rejects_incompatible_embedding_contract(tmp_path):
    path = tmp_path / "store.json"
    make_store().save(path)

    with pytest.raises(ValueError, match="embedding id mismatch"):
        VectorStore.load(
            path,
            embedding_id="another-model-v2",
            dimension=HASH_DIMENSION,
        )
    with pytest.raises(ValueError, match="embedding dimension mismatch"):
        VectorStore.load(
            path,
            embedding_id=HASH_EMBEDDING_ID,
            dimension=HASH_DIMENSION + 1,
        )


def test_load_rejects_unknown_schema_and_malformed_items(tmp_path):
    path = tmp_path / "store.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 999,
                "embedding": {
                    "id": HASH_EMBEDDING_ID,
                    "dimension": HASH_DIMENSION,
                },
                "items": [],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unsupported schema_version"):
        VectorStore.load(
            path,
            embedding_id=HASH_EMBEDDING_ID,
            dimension=HASH_DIMENSION,
        )

    path.write_text(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "embedding": {
                    "id": HASH_EMBEDDING_ID,
                    "dimension": HASH_DIMENSION,
                },
                "items": [{"record": SAMPLE_RECORDS[0], "vector": [1.0]}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="dimension"):
        VectorStore.load(
            path,
            embedding_id=HASH_EMBEDDING_ID,
            dimension=HASH_DIMENSION,
        )


def test_equal_scores_keep_insertion_order():
    records = [
        {"id": "first", "source": "a.md", "text": "общий первый"},
        {"id": "second", "source": "b.md", "text": "общий второй"},
    ]
    store = make_store(records)

    hits = store.query(hash_embed("общий"), k=2)

    assert [hit["id"] for hit in hits] == ["first", "second"]
