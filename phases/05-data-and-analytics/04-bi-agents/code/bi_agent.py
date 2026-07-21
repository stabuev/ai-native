"""BI-агент: выбирает шаги анализа — Build It для урока 5.4.

Без зависимостей. Агент-планировщик строит план BI-расследования (обзор →
разбивка по измерению → топ-сегмент с долей) и исполняет его на данных.
Policy детерминированная (офлайн); в USE IT шаги выбирает LLM (Genie/Spotter/Hex).
"""


def _aggregate(rows, group_by, value):
    out = {}
    for r in rows:
        out[r[group_by]] = out.get(r[group_by], 0.0) + float(r[value])
    return out


def investigate(rows, dimension, value):
    """План расследования: overview → breakdown → top_segment. Возвращает шаги."""
    total = sum(float(r[value]) for r in rows)
    by_dim = _aggregate(rows, dimension, value)
    top_key, top_val = max(by_dim.items(), key=lambda kv: kv[1])
    return [
        {"step": "overview", "total": total},
        {"step": "breakdown", "by": dimension, "values": by_dim},
        {"step": "top_segment", "segment": top_key, "value": top_val,
         "share": round(top_val / total, 3) if total else 0.0},
    ]


DEMO = [
    {"region": "Москва", "amount": "150"},
    {"region": "Питер", "amount": "100"},
    {"region": "Казань", "amount": "20"},
]

if __name__ == "__main__":
    for step in investigate(DEMO, "region", "amount"):
        print(step)
