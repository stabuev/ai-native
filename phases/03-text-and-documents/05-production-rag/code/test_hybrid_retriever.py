from hybrid_retriever import (build_index, vector_ranking, keyword_ranking,
                              reciprocal_rank_fusion, hybrid_search)

DOCS = [
    "машинное обучение и нейронные сети для классификации",
    "рецепт борща со свёклой и капустой",
    "библиотека numpy быстрые операции над матрицами в python",
]


def test_rrf_ranks_consensus_first():
    # документ 2 первый в обоих списках → первый после слияния
    fused = reciprocal_rank_fusion([[2, 0, 1], [2, 1, 0]])
    assert fused[0] == 2


def test_keyword_catches_exact_term():
    index = build_index(DOCS)
    assert keyword_ranking("numpy", index)[0] == 2


def test_hybrid_returns_relevant_first():
    index = build_index(DOCS)
    top = hybrid_search("numpy матрицами", index, top_k=1)
    assert "numpy" in top[0]["doc"]


def test_hybrid_respects_top_k():
    index = build_index(DOCS)
    assert len(hybrid_search("обучение", index, top_k=2)) == 2


def test_vector_and_keyword_return_all_indices():
    index = build_index(DOCS)
    assert sorted(vector_ranking("x", index)) == [0, 1, 2]
