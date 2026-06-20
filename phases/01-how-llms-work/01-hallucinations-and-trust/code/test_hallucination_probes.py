from hallucination_probes import PROBES, evaluate_response, trust_score

BY_ID = {p["id"]: p for p in PROBES}


def test_unanswerable_refusal_passes_but_confident_answer_fails():
    p = BY_ID["fake-fact"]
    assert evaluate_response(p, "Такого города не существует, данных нет.")["ok"]
    assert not evaluate_response(p, "Население составляет 1 234 567 человек.")["ok"]


def test_false_premise_must_be_challenged():
    p = BY_ID["false-premise"]
    assert evaluate_response(p, "На самом деле башня из железа, предпосылка неверна.")["ok"]
    assert not evaluate_response(p, "Потому что золото красиво блестит на солнце.")["ok"]


def test_answerable_should_not_refuse():
    p = BY_ID["answerable"]
    assert evaluate_response(p, "Будет 4.")["ok"]
    assert not evaluate_response(p, "Не знаю, не могу ответить.")["ok"]


def test_trust_score_aggregates():
    good = {"fake-fact": "не существует", "false-premise": "неверно, на самом деле железо",
            "future": "неизвестно", "answerable": "4"}
    results = [evaluate_response(p, good[p["id"]]) for p in PROBES]
    assert trust_score(results) == 1.0
    bad = [evaluate_response(p, "уверенный ответ") for p in PROBES]
    assert trust_score(bad) < 1.0
