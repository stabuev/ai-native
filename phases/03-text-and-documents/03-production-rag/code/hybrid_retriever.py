"""Production RAG: гибридный ретривер (vector+keyword) + RRF-reranking — Build It 3.5.

Без зависимостей. Чистый vector-RAG (3.3) промахивается на точных терминах/кодах,
keyword — на синонимах. Прод-RAG объединяет оба сигнала и переранжирует слиянием
рангов (Reciprocal Rank Fusion). В USE IT — managed retrieval / GraphRAG + RAGAS.
"""
import math
import re
from collections import Counter


def _tok(text):
    return re.findall(r"\w+", text.lower())


def build_index(docs):
    toks = [_tok(d) for d in docs]
    df = Counter()
    for t in toks:
        df.update(set(t))
    n = len(docs)
    idf = {w: math.log((n + 1) / (c + 1)) + 1 for w, c in df.items()}

    def vec(t):
        tf = Counter(t)
        total = sum(tf.values()) or 1
        return {w: (c / total) * idf.get(w, 0.0) for w, c in tf.items()}

    return {"docs": list(docs), "idf": idf, "vecs": [vec(t) for t in toks]}


def _cos(a, b):
    common = set(a) & set(b)
    dot = sum(a[w] * b[w] for w in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def vector_ranking(query, index):
    """Индексы документов по убыванию косинусной близости (семантика)."""
    qtf = Counter(_tok(query))
    total = sum(qtf.values()) or 1
    qv = {w: (c / total) * index["idf"].get(w, 0.0) for w, c in qtf.items()}
    return sorted(range(len(index["docs"])),
                  key=lambda i: _cos(qv, index["vecs"][i]), reverse=True)


def keyword_ranking(query, index):
    """Индексы документов по числу точных совпадений слов (лексика)."""
    q = set(_tok(query))
    return sorted(range(len(index["docs"])),
                  key=lambda i: len(q & set(_tok(index["docs"][i]))), reverse=True)


def reciprocal_rank_fusion(rankings, k=60):
    """Слить несколько ранжирований в одно (RRF): score = sum 1/(k + rank)."""
    scores = Counter()
    for ranking in rankings:
        for rank, idx in enumerate(ranking):
            scores[idx] += 1 / (k + rank + 1)
    return [idx for idx, _ in scores.most_common()]


def hybrid_search(query, index, top_k=3):
    """Гибрид: vector + keyword, переранжированные через RRF."""
    fused = reciprocal_rank_fusion([vector_ranking(query, index), keyword_ranking(query, index)])
    return [{"doc": index["docs"][i]} for i in fused[:top_k]]


if __name__ == "__main__":
    docs = [
        "машинное обучение и нейронные сети для классификации",
        "рецепт борща со свёклой и капустой",
        "библиотека numpy: быстрые операции над матрицами в python",
    ]
    index = build_index(docs)
    for hit in hybrid_search("numpy матрицы", index, top_k=2):
        print(hit["doc"])
