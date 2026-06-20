import pytest
from chunking import chunk_text, map_reduce

TEXT = " ".join(f"w{i}" for i in range(1, 26))   # w1..w25, 25 слов


def test_chunks_respect_size():
    chunks = chunk_text(TEXT, size=10, overlap=3)
    assert all(len(c.split()) <= 10 for c in chunks)


def test_chunks_cover_all_words():
    chunks = chunk_text(TEXT, size=10, overlap=3)
    seen = set()
    for c in chunks:
        seen.update(c.split())
    assert seen == set(TEXT.split())          # ни одно слово не потеряно
    assert chunks[0].split()[0] == "w1"
    assert chunks[-1].split()[-1] == "w25"


def test_overlap_between_consecutive_chunks():
    chunks = chunk_text(TEXT, size=10, overlap=3)
    first, second = chunks[0].split(), chunks[1].split()
    assert first[-3:] == second[:3]           # последние 3 = первые 3 следующего


def test_invalid_params_raise():
    with pytest.raises(ValueError):
        chunk_text(TEXT, size=0)
    with pytest.raises(ValueError):
        chunk_text(TEXT, size=5, overlap=5)


def test_map_reduce_composes():
    chunks = chunk_text(TEXT, size=10, overlap=0)
    total = map_reduce(chunks, lambda c: len(c.split()), sum)
    assert total == 25                        # без перекрытия слова не дублируются


def test_empty_text():
    assert chunk_text("", size=10, overlap=2) == []
