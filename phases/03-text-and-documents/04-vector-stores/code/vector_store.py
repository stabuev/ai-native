"""Векторное хранилище с нуля — Build It для урока 3.4.

Без зависимостей. Мини-хранилище как у Chroma/FAISS, только маленькое:
добавляем документы (эмбеддинг = хеширующий bag-of-words в фикс. размер),
ищем по косинусу, сохраняем/грузим на диск. Хеш детерминированный — результат
воспроизводим между запусками и после load.
"""
import json
import math
import re

DIM = 256


def _stable_hash(word):
    """Детерминированный хеш слова (встроенный hash() рандомизирован — нельзя)."""
    h = 0
    for ch in word:
        h = (h * 31 + ord(ch)) % (2 ** 32)
    return h


def embed(text):
    """Хеширующий эмбеддинг: слова раскладываются по DIM бакетам."""
    vec = [0.0] * DIM
    for w in re.findall(r"\w+", text.lower()):
        vec[_stable_hash(w) % DIM] += 1.0
    return vec


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class VectorStore:
    """Минимальное векторное хранилище: add / query / save / load."""

    def __init__(self):
        self.items = []      # [{id, text, vec}]

    def add(self, id, text):
        self.items.append({"id": id, "text": text, "vec": embed(text)})

    def query(self, text, k=3):
        qv = embed(text)
        scored = sorted(
            ((cosine(qv, it["vec"]), it) for it in self.items),
            key=lambda x: x[0], reverse=True,
        )
        return [{"id": it["id"], "text": it["text"], "score": round(s, 4)}
                for s, it in scored[:k]]

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.items, f, ensure_ascii=False)

    def load(self, path):
        with open(path, encoding="utf-8") as f:
            self.items = json.load(f)
        return self


if __name__ == "__main__":
    store = VectorStore()
    for i, doc in enumerate([
        "кошки любят спать и рыбу",
        "собаки любят прогулки и мяч",
        "python язык программирования",
    ]):
        store.add(f"doc{i}", doc)
    for hit in store.query("кошки и рыба", k=2):
        print(f"{hit['score']:.3f}  {hit['id']}: {hit['text']}")
