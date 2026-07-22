import pytest

from tokenizer import decode, encode, train_bpe

CORPUS = [
    "low lower lowest",
    "newer wider newest",
    "low low low newer newer wider",
]


def test_learns_the_most_frequent_pair_first():
    # В "abab" пара ab встречается дважды, в "ab" — ещё один раз.
    assert train_bpe(["abab", "ab"], num_merges=1) == [(b"a", b"b")]


def test_encode_applies_a_merge_to_every_non_overlapping_occurrence():
    assert encode("abab", [(b"a", b"b")]) == [b"ab", b"ab"]


def test_merge_rules_are_applied_in_learned_order():
    merges = [(b"a", b"b"), (b"ab", b"c")]
    assert encode("abc", merges) == [b"abc"]


def test_roundtrip_preserves_unicode_and_whitespace_exactly():
    text = "  Привет,\nAI 👋  "
    merges = train_bpe([text, text], num_merges=20)
    assert decode(encode(text, merges)) == text


def test_bpe_reduces_token_count():
    merges = train_bpe(CORPUS, num_merges=10)
    baseline = encode("lower", [])
    learned = encode("lower", merges)
    assert len(learned) < len(baseline)


def test_more_merges_never_increases_tokens():
    few = train_bpe(CORPUS, 2)
    many = train_bpe(CORPUS, 12)
    assert len(encode("lowest", many)) <= len(encode("lowest", few))


def test_negative_number_of_merges_is_rejected():
    with pytest.raises(ValueError, match="num_merges"):
        train_bpe(CORPUS, -1)
