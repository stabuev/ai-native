from tokenizer import train_bpe, encode, decode

CORPUS = [
    "low lower lowest",
    "newer wider newest",
    "low low low newer newer wider",
]


def test_roundtrip():
    merges = train_bpe(CORPUS, num_merges=10)
    text = "low newer wider"
    assert decode(encode(text, merges)) == text


def test_bpe_reduces_token_count():
    merges = train_bpe(CORPUS, num_merges=10)
    baseline = encode("lower", [])      # символы + </w>
    learned = encode("lower", merges)
    assert len(learned) <= len(baseline)


def test_learns_some_merges():
    merges = train_bpe(CORPUS, num_merges=5)
    assert len(merges) > 0


def test_more_merges_never_increases_tokens():
    few = train_bpe(CORPUS, 2)
    many = train_bpe(CORPUS, 12)
    assert len(encode("lowest", many)) <= len(encode("lowest", few))
