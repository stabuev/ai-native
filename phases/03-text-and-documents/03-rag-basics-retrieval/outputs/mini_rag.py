"""mini_rag.py — артефакт урока 3.3: самодостаточный RAG-скелет (retrieve → augment).

Без зависимостей и без сети. TF-IDF retrieval + сборка промпта с контекстом.
Шаг generate оставлен заглушкой: подставь вызов модели (Claude/OpenAI/Gemini).

Запуск:  python mini_rag.py
"""
import math
import re
from collections import Counter


def _tokens(t):
    return re.findall(r"\w+", t.lower())


def _tfidf(tokens, idf):
    tf = Counter(tokens)
    total = sum(tf.values()) or 1
    return {w: (c / total) * idf.get(w, 0.0) for w, c in tf.items()}


def build_index(docs):
    toks = [_tokens(d) for d in docs]
    df = Counter()
    for t in toks:
        df.update(set(t))
    n = len(docs)
    idf = {w: math.log((n + 1) / (c + 1)) + 1 for w, c in df.items()}
    return {"docs": list(docs), "idf": idf, "vectors": [_tfidf(t, idf) for t in toks]}


def _cosine(a, b):
    dot = sum(a[w] * b[w] for w in set(a) & set(b))
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def retrieve(query, index, k=3):
    qv = _tfidf(_tokens(query), index["idf"])
    scored = sorted(((_cosine(qv, v), i) for i, v in enumerate(index["vectors"])),
                    key=lambda x: x[0], reverse=True)
    return [index["docs"][i] for s, i in scored[:k] if s > 0]


def build_prompt(query, contexts):
    """augment: собрать промпт с найденным контекстом и требованием отвечать по нему."""
    ctx = "\n".join(f"- {c}" for c in contexts) or "(контекст не найден)"
    return (f"Ответь на вопрос ТОЛЬКО по контексту ниже. "
            f"Если ответа в контексте нет — скажи «не знаю».\n\n"
            f"Контекст:\n{ctx}\n\nВопрос: {query}\nОтвет:")


def answer(query, index, generate=None, k=3):
    """retrieve → augment → generate. generate(prompt)->str; по умолчанию вернёт промпт."""
    contexts = retrieve(query, index, k)
    prompt = build_prompt(query, contexts)
    if generate is None:
        return prompt                      # без модели показываем готовый промпт
    return generate(prompt)


if __name__ == "__main__":
    corpus = [
        "Возврат товара возможен в течение 14 дней с момента покупки.",
        "Гарантия на электронику составляет 12 месяцев.",
        "Доставка по городу занимает 1-2 рабочих дня.",
    ]
    index = build_index(corpus)
    print(answer("сколько дней на возврат?", index))
    # с моделью:  answer(q, index, generate=lambda p: client.messages.create(...))
