from inference_loop import train_ngram, next_token_probs, generate

CORPUS = [
    ["a", "b", "c", "x"],
    ["a", "b", "c", "x"],
    ["q", "b", "c", "y"],
]


def test_probs_sum_to_one():
    m = train_ngram(CORPUS, order=3)
    probs = next_token_probs(m, ["b", "c"])
    assert abs(sum(probs.values()) - 1.0) < 1e-9
    assert probs == {"x": 2 / 3, "y": 1 / 3}


def test_backoff_to_shorter_suffix():
    m = train_ngram(CORPUS, order=3)
    # ("z","c") нет в модели → backoff к ("c",)
    assert next_token_probs(m, ["z", "c"]) == next_token_probs(m, ["c"])


def test_greedy_is_deterministic():
    m = train_ngram(CORPUS, order=3)
    assert generate(m, ["a", "b", "c"], max_tokens=1) == generate(m, ["a", "b", "c"], max_tokens=1)


def test_context_window_changes_output():
    m = train_ngram(CORPUS, order=3)
    full = generate(m, ["q", "b", "c"], max_tokens=1, window=8)   # видит ("q","b","c") → y
    narrow = generate(m, ["q", "b", "c"], max_tokens=1, window=2)  # видит ("b","c") → x
    assert full == ["y"]
    assert narrow == ["x"]


def test_unknown_context_stops():
    m = train_ngram(CORPUS, order=3)
    assert generate(m, ["zzz"], max_tokens=5) == []
