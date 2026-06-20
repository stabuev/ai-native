import random
from sampling import softmax, top_k_filter, top_p_filter, sample, entropy

LOGITS = [3.0, 2.0, 1.0, 0.0]


def test_softmax_sums_to_one_and_temp0_is_onehot():
    p = softmax(LOGITS, 1.0)
    assert abs(sum(p) - 1.0) < 1e-9
    p0 = softmax(LOGITS, 0.0)
    assert p0 == [1.0, 0.0, 0.0, 0.0]


def test_higher_temperature_increases_entropy():
    assert entropy(softmax(LOGITS, 2.0)) > entropy(softmax(LOGITS, 0.5))


def test_top_k_keeps_exactly_k():
    filt = top_k_filter(softmax(LOGITS, 1.0), 2)
    assert sum(1 for x in filt if x > 0) == 2
    assert abs(sum(filt) - 1.0) < 1e-9


def test_top_p_keeps_minimal_nucleus():
    filt = top_p_filter(softmax(LOGITS, 1.0), 0.5)
    nonzero = sum(1 for x in filt if x > 0)
    assert 1 <= nonzero <= 2            # самый вероятный уже ~0.64
    assert abs(sum(filt) - 1.0) < 1e-9


def test_temperature_zero_is_deterministic_argmax():
    assert all(sample(LOGITS, 0.0) == 0 for _ in range(5))
    assert sample(LOGITS, 0.0, top_k=1) == 0


def test_seeded_sampling_is_reproducible():
    a = [sample(LOGITS, 1.0, rng=random.Random(7)) for _ in range(5)]
    b = [sample(LOGITS, 1.0, rng=random.Random(7)) for _ in range(5)]
    assert a == b


def test_top_k_1_forces_argmax():
    assert all(sample(LOGITS, 1.0, top_k=1, rng=random.Random(i)) == 0 for i in range(5))
