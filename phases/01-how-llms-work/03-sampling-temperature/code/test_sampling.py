import random

import pytest

from sampling import sample, softmax, top_k_filter, top_p_filter


LOGITS = [3.0, 2.0, 1.0, 0.0]


class FixedRng:
    def __init__(self, draw):
        self.draw = draw
        self.calls = 0

    def random(self):
        self.calls += 1
        return self.draw


class ForbiddenRng:
    def random(self):
        raise AssertionError("temperature=0 must not call the random generator")


def test_softmax_matches_worked_example_and_sums_to_one():
    probs = softmax(LOGITS, 1.0)

    assert probs == pytest.approx(
        [0.643914, 0.236883, 0.087144, 0.032059],
        abs=1e-6,
    )
    assert sum(probs) == pytest.approx(1.0)


def test_temperature_changes_distribution_not_ranking():
    cold = softmax(LOGITS, 0.5)
    hot = softmax(LOGITS, 2.0)

    assert cold[0] > hot[0]
    assert cold[-1] < hot[-1]
    assert max(range(len(cold)), key=cold.__getitem__) == 0
    assert max(range(len(hot)), key=hot.__getitem__) == 0


def test_softmax_is_stable_for_large_logits():
    probs = softmax([1001.0, 1000.0])

    assert probs == pytest.approx([0.731059, 0.268941], abs=1e-6)
    assert sum(probs) == pytest.approx(1.0)


def test_top_k_keeps_exact_positions_and_renormalizes():
    filtered = top_k_filter([0.64, 0.24, 0.09, 0.03], 2)

    assert filtered == pytest.approx([0.64 / 0.88, 0.24 / 0.88, 0.0, 0.0])
    assert sum(filtered) == pytest.approx(1.0)


def test_top_p_adapts_nucleus_size_to_distribution_shape():
    confident = top_p_filter([0.64, 0.24, 0.09, 0.03], 0.8)
    flat = top_p_filter([0.35, 0.30, 0.20, 0.15], 0.8)

    assert confident == pytest.approx([0.64 / 0.88, 0.24 / 0.88, 0.0, 0.0])
    assert flat == pytest.approx([0.35 / 0.85, 0.30 / 0.85, 0.20 / 0.85, 0.0])
    assert sum(value > 0 for value in confident) == 2
    assert sum(value > 0 for value in flat) == 3


def test_temperature_zero_returns_argmax_without_random_draw():
    assert sample(LOGITS, temperature=0, rng=ForbiddenRng()) == 0


def test_top_k_one_forces_argmax_even_with_sampling():
    rng = FixedRng(0.999)

    assert sample(LOGITS, temperature=1.0, top_k=1, rng=rng) == 0
    assert rng.calls == 1


def test_fixed_draw_selects_by_cumulative_probability():
    rng = FixedRng(0.8)

    assert sample(LOGITS, temperature=1.0, top_k=2, rng=rng) == 1
    assert rng.calls == 1


def test_filtered_positions_are_never_sampled():
    chosen = {
        sample(LOGITS, temperature=2.0, top_k=2, rng=random.Random(seed))
        for seed in range(50)
    }

    assert chosen <= {0, 1}
    assert chosen == {0, 1}


def test_same_seed_reproduces_a_sequence_when_generator_is_reused():
    first_rng = random.Random(7)
    second_rng = random.Random(7)

    first = [sample([0.0, 0.0, 0.0, 0.0], rng=first_rng) for _ in range(12)]
    second = [sample([0.0, 0.0, 0.0, 0.0], rng=second_rng) for _ in range(12)]

    assert first == second
    assert len(set(first)) > 1


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda: softmax([], 1.0), "logits"),
        (lambda: softmax(LOGITS, 0.0), "greater than zero"),
        (lambda: sample(LOGITS, temperature=-0.1), "negative"),
        (lambda: top_k_filter([0.5, 0.5], 0), "positive integer"),
        (lambda: top_k_filter([0.5, 0.5], 1.5), "positive integer"),
        (lambda: top_k_filter([0.5, 0.5], 3.5), "positive integer"),
        (lambda: top_p_filter([0.5, 0.5], 0.0), "interval"),
        (lambda: top_p_filter([0.5, 0.5], True), "interval"),
        (lambda: top_p_filter([0.5, -0.5], 0.8), "non-negative"),
        (lambda: top_p_filter([0.0, 0.0], 0.8), "positive sum"),
    ],
)
def test_invalid_inputs_fail_explicitly(call, message):
    with pytest.raises(ValueError, match=message):
        call()
