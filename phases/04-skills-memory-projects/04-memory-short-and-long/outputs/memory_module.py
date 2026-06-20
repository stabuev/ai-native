"""Память агента: короткая и длинная — Build It для урока 4.2.

Без зависимостей. Файловое хранилище памяти с поиском и темпоральностью:
добавляем записи с меткой времени, ищем по релевантности С УЧЁТОМ свежести,
сохраняем/грузим на диск. Это «память» агента в простейшем виде (мост к Фазе 7).
"""
import json
import re
import time


def _words(text):
    return set(re.findall(r"\w+", text.lower()))


class MemoryStore:
    """Память с релевантностью (совпадение слов) и темпоральностью (свежесть)."""

    def __init__(self, half_life=30.0):
        self.items = []                 # [{id, text, ts, tags}]
        self.half_life = half_life      # период полураспада «свежести»

    def add(self, text, tags=None, ts=None):
        item = {"id": len(self.items), "text": text,
                "ts": time.time() if ts is None else ts, "tags": tags or []}
        self.items.append(item)
        return item

    def search(self, query, k=3, now=None):
        """Топ-k записей: релевантность (совпадение слов) + свежесть (затухание)."""
        q = _words(query)
        now = time.time() if now is None else now
        scored = []
        for it in self.items:
            overlap = len(q & _words(it["text"]))
            if overlap == 0:
                continue
            age = max(0.0, now - it["ts"])
            recency = 0.5 ** (age / self.half_life)     # 1.0 для свежего, → 0 для старого
            scored.append((overlap + recency, it))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [it for _, it in scored[:k]]

    def recent(self, n=5):
        return sorted(self.items, key=lambda it: it["ts"], reverse=True)[:n]

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.items, f, ensure_ascii=False)

    def load(self, path):
        with open(path, encoding="utf-8") as f:
            self.items = json.load(f)
        return self


if __name__ == "__main__":
    m = MemoryStore(half_life=30.0)
    now = 1000.0
    m.add("пользователь любит кофе без сахара", ts=now - 100)
    m.add("пользователь снова заказал кофе латте", ts=now - 1)
    m.add("обсуждали отпуск в горах", ts=now - 5)
    print("Поиск 'кофе':")
    for it in m.search("кофе", now=now):
        print("  ", it["text"])
