"""ИИ как аналитик: мини-аналитика на stdlib под планом — Build It для урока 5.1.

Без внешних зависимостей. Промпт превращается в план анализа (что сгруппировать,
какую метрику, как агрегировать), а тулкит его исполняет — как делает ИИ-аналитик,
только мы видим механизм. В USE IT тот же план исполняет pandas / Code Interpreter.
"""
import csv
import io
from statistics import mean


def load_csv(text):
    """CSV-текст -> список словарей (строки таблицы)."""
    return list(csv.DictReader(io.StringIO(text.strip())))


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def aggregate(rows, group_by, value, agg="sum"):
    """Сгруппировать rows по group_by и агрегировать value (sum/mean/count)."""
    groups = {}
    for r in rows:
        groups.setdefault(r.get(group_by), []).append(r)
    out = {}
    for key, items in groups.items():
        nums = [n for n in (_num(i.get(value)) for i in items) if n is not None]
        if agg == "count":
            out[key] = len(items)
        elif agg == "mean":
            out[key] = mean(nums) if nums else 0.0
        else:  # sum
            out[key] = sum(nums)
    return out


def top_n(d, n=3):
    """Топ-n пар (ключ, значение) по убыванию значения."""
    return sorted(d.items(), key=lambda kv: kv[1], reverse=True)[:n]


CSV_DEMO = """region,product,amount
Москва,A,100
Москва,B,50
Питер,A,30
Питер,B,70
Казань,A,20
"""

if __name__ == "__main__":
    rows = load_csv(CSV_DEMO)
    by_region = aggregate(rows, "region", "amount", "sum")
    print("Выручка по регионам:", by_region)
    print("Топ-2 региона:", top_n(by_region, 2))
    print("Средний чек по продукту:", aggregate(rows, "product", "amount", "mean"))
