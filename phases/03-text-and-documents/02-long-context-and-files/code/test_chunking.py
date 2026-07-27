import pytest

from chunking import (
    chunk_text,
    hierarchical_reduce,
    map_chunks,
    map_reduce,
)


TEXT = " ".join(f"w{i}" for i in range(1, 26))


def test_chunks_have_stable_ids_positions_and_expected_overlap():
    chunks = chunk_text(TEXT, size=10, overlap=3, source="report")

    assert [chunk["word_start"] for chunk in chunks] == [0, 7, 14, 21]
    assert [chunk["word_end"] for chunk in chunks] == [10, 17, 24, 25]
    assert chunks[0]["id"] == "report#chunk-0000"
    assert chunks[-1]["source"] == "report"
    assert chunks[0]["text"].split()[-3:] == chunks[1]["text"].split()[:3]


def test_ordered_reconstruction_proves_no_words_were_lost():
    overlap = 3
    chunks = chunk_text(TEXT, size=10, overlap=overlap)
    reconstructed = chunks[0]["text"].split()
    for chunk in chunks[1:]:
        reconstructed.extend(chunk["text"].split()[overlap:])

    assert reconstructed == TEXT.split()


def test_invalid_size_or_overlap_is_rejected_before_data_loss():
    invalid_params = [
        {"size": 0, "overlap": 0},
        {"size": 5, "overlap": -1},
        {"size": 5, "overlap": 5},
        {"size": 5, "overlap": 6},
        {"size": 5.0, "overlap": 1},
    ]
    for params in invalid_params:
        with pytest.raises(ValueError):
            chunk_text(TEXT, **params)


def test_empty_text_returns_no_chunks():
    assert chunk_text(" \n ", size=10, overlap=2) == []


def test_map_preserves_the_origin_of_every_summary():
    chunks = chunk_text(TEXT, size=8, overlap=0, source="minutes")
    mapped = map_chunks(chunks, lambda text: text.split()[0])

    assert [item["chunk_ids"] for item in mapped] == [
        [chunk["id"]] for chunk in chunks
    ]
    assert all(item["level"] == 0 for item in mapped)


def test_empty_map_result_is_not_silently_passed_to_reduce():
    chunks = chunk_text(TEXT, size=10, overlap=0)

    with pytest.raises(ValueError, match="map_fn returned empty"):
        map_chunks(chunks, lambda text: "")


def test_hierarchical_reduce_bounds_every_call_and_preserves_provenance():
    chunks = chunk_text(TEXT, size=3, overlap=0, source="report")
    mapped = map_chunks(chunks, lambda text: text)
    observed_batch_sizes = []

    def reduce_fn(parts):
        observed_batch_sizes.append(len(parts))
        return " | ".join(parts)

    trace = hierarchical_reduce(mapped, reduce_fn, fan_in=3)

    assert len(trace["levels"]) > 2
    assert all(2 <= size <= 3 for size in observed_batch_sizes)
    assert trace["result"]["chunk_ids"] == [chunk["id"] for chunk in chunks]
    assert len(trace["levels"][-1]) == 1


def test_map_reduce_composes_and_empty_input_has_no_fake_result():
    chunks = chunk_text(TEXT, size=5, overlap=0)
    observed_batch_sizes = []

    def reduce_lengths(parts):
        observed_batch_sizes.append(len(parts))
        return str(sum(map(int, parts)))

    trace = map_reduce(
        chunks,
        map_fn=lambda text: str(len(text.split())),
        reduce_fn=reduce_lengths,
        fan_in=2,
    )

    assert trace["result"]["text"] == "25"
    assert observed_batch_sizes and set(observed_batch_sizes) == {2}
    assert map_reduce([], str, lambda parts: "unexpected") == {
        "result": None,
        "levels": [],
    }


def test_fan_in_one_cannot_make_progress():
    mapped = map_chunks(
        chunk_text(TEXT, size=5, overlap=0),
        lambda text: text,
    )

    with pytest.raises(ValueError, match="at least 2"):
        hierarchical_reduce(mapped, lambda parts: " ".join(parts), fan_in=1)
