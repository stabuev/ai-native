from retriever import build_index, search

CORPUS = [
    "Python — язык программирования общего назначения.",
    "Кошки домашние животные и любят спать днём.",
    "Машинное обучение использует данные для предсказаний.",
    "Собаки верные домашние животные и любят прогулки.",
]


def test_relevant_doc_ranked_first():
    index = build_index(CORPUS)
    hits = search("язык программирования", index, k=1)
    assert "Python" in hits[0]["doc"]


def test_topk_limits_results():
    index = build_index(CORPUS)
    assert len(search("животные", index, k=2)) == 2


def test_animals_query_prefers_animal_docs():
    index = build_index(CORPUS)
    top2 = [h["doc"] for h in search("домашние животные", index, k=2)]
    assert all("животные" in d for d in top2)     # кошки и собаки выше Python/ML


def test_no_match_scores_zero():
    index = build_index(CORPUS)
    hits = search("квантовая криптография блокчейн", index, k=1)
    assert hits[0]["score"] == 0.0
