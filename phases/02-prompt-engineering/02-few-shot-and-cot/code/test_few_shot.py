from few_shot import format_few_shot, format_cot, knn_predict, zero_shot_predict, accuracy

EXAMPLES = [
    ("обожаю прекрасный фильм", "pos"),
    ("чудесный замечательный день", "pos"),
    ("ненавижу отвратительную еду", "neg"),
    ("ужасный кошмарный сервис", "neg"),
]
TEST = [("обожаю прекрасный сериал", "pos"), ("ужасный кошмарный продукт", "neg")]


def test_few_shot_prompt_contains_examples_and_query():
    p = format_few_shot("Классифицируй.", EXAMPLES, "новый текст")
    assert "обожаю прекрасный фильм" in p
    assert p.rstrip().endswith("Выход:")
    assert "новый текст" in p


def test_cot_prompt_asks_for_steps():
    p = format_cot("Реши задачу.", "2+2*2")
    assert "по шагам" in p.lower()


def test_few_shot_beats_zero_shot():
    few = accuracy(lambda x: knn_predict(x, EXAMPLES), TEST)
    zero = accuracy(lambda x: zero_shot_predict(x, "neg"), TEST)
    assert few > zero
    assert few == 1.0


def test_knn_uses_most_similar_example():
    assert knn_predict("обожаю прекрасный сюжет", EXAMPLES) == "pos"
    assert knn_predict("ужасный кошмарный интерфейс", EXAMPLES) == "neg"
