"""RAG retrieval: TF-IDF ретривер с нуля — Build It для урока 3.3.

Без зависимостей. «Эмбеддинг» здесь — TF-IDF вектор слова; близость — косинус.
Принцип тот же, что у настоящего RAG: представить тексты числами и найти
ближайшие к запросу. В USE IT TF-IDF заменяется на нейроэмбеддинги.
"""
import math
import re
from collections import Counter


def _tokens(text):
    return re.findall(r"\w+", text.lower())


def _tfidf(tokens, idf):
    tf = Counter(tokens)
    total = sum(tf.values()) or 1
    return {w: (c / total) * idf.get(w, 0.0) for w, c in tf.items()}


def build_index(docs):
    """docs: list[str] -> индекс с idf и tf-idf векторами документов."""
    toks = [_tokens(d) for d in docs]
    df = Counter()
    for t in toks:
        df.update(set(t))
    n = len(docs)
    idf = {w: math.log((n + 1) / (c + 1)) + 1 for w, c in df.items()}
    return {"docs": list(docs), "idf": idf, "vectors": [_tfidf(t, idf) for t in toks]}


def _cosine(a, b):
    common = set(a) & set(b)
    dot = sum(a[w] * b[w] for w in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def search(query, index, k=3):
    """Топ-k документов по косинусной близости к запросу."""
    qv = _tfidf(_tokens(query), index["idf"])
    scored = sorted(
        ((_cosine(qv, v), i) for i, v in enumerate(index["vectors"])),
        key=lambda x: x[0], reverse=True,
    )
    return [{"doc": index["docs"][i], "score": round(s, 4)} for s, i in scored[:k]]


if __name__ == "__main__":
    corpus = [
        "Python — язык программирования общего назначения.",
        "Кошки — домашние животные, любят спать днём.",
        "Машинное обучение использует данные для предсказаний.",
        "Собаки — верные домашние животные и любят прогулки.",
    ]
    index = build_index(corpus)
    for q in ["домашние животные", "язык программирования"]:
        print(f"\nЗапрос: {q}")
        for hit in search(q, index, k=2):
            print(f"  {hit['score']:.3f}  {hit['doc']}")
