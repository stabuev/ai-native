import pytest

from inference_loop import generate, greedy_next_token, visible_context


WINDOW_MODEL = {
    ("remember", "blue"): {"sky": 0.9, "sea": 0.1},
    ("blue",): {"sky": 0.2, "sea": 0.8},
    ("blue", "sky"): {"<STOP>": 1.0},
    ("sky",): {"<STOP>": 1.0},
    ("sea",): {"<STOP>": 1.0},
}


def test_visible_context_returns_only_tokens_inside_window():
    context = ["system", "old", "current"]

    assert visible_context(context, 2) == ["old", "current"]
    assert visible_context(context, 10) == context
    assert visible_context(context, 2) is not context


def test_visible_context_rejects_non_positive_window():
    with pytest.raises(ValueError, match="window"):
        visible_context(["token"], 0)


def test_greedy_selects_highest_probability():
    probabilities = {"likely": 0.65, "plausible": 0.25, "rare": 0.10}

    assert greedy_next_token(probabilities) == "likely"


def test_greedy_rejects_missing_distribution():
    with pytest.raises(ValueError, match="probabilities"):
        greedy_next_token({})


def test_context_window_changes_first_generated_token():
    prompt = ["remember", "blue"]

    wide = generate(WINDOW_MODEL, prompt, max_new_tokens=1, window=2)
    narrow = generate(WINDOW_MODEL, prompt, max_new_tokens=1, window=1)

    assert wide["trace"][0]["visible_context"] == ["remember", "blue"]
    assert narrow["trace"][0]["visible_context"] == ["blue"]
    assert wide["tokens"] == ["sky"]
    assert narrow["tokens"] == ["sea"]


def test_generated_token_becomes_context_for_next_step():
    model = {
        ("start",): {"middle": 0.8, "other": 0.2},
        ("middle",): {"finish": 0.7, "other": 0.3},
    }

    result = generate(model, ["start"], max_new_tokens=2, window=1)

    assert result["tokens"] == ["middle", "finish"]
    assert result["trace"][1]["visible_context"] == ["middle"]
    assert result["stop_reason"] == "max_new_tokens"


def test_stop_token_ends_generation_without_leaking_into_output():
    result = generate(WINDOW_MODEL, ["remember", "blue"], 3, window=2)

    assert result["tokens"] == ["sky"]
    assert result["trace"][-1]["chosen_token"] == "<STOP>"
    assert result["stop_reason"] == "stop_token"


def test_unknown_context_has_explicit_stop_reason():
    result = generate(WINDOW_MODEL, ["unknown"], 3, window=1)

    assert result == {
        "tokens": [],
        "trace": [],
        "stop_reason": "no_distribution",
    }


def test_max_new_tokens_is_a_hard_limit():
    looping_model = {("again",): {"again": 1.0}}

    result = generate(looping_model, ["again"], max_new_tokens=3, window=1)

    assert result["tokens"] == ["again", "again", "again"]
    assert len(result["trace"]) == 3
    assert result["stop_reason"] == "max_new_tokens"


def test_negative_generation_limit_is_rejected():
    with pytest.raises(ValueError, match="max_new_tokens"):
        generate(WINDOW_MODEL, ["blue"], max_new_tokens=-1, window=1)
