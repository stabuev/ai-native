"""FinOps для ИИ: тегирование, учёт, ROI — Build It для урока 9.4.

Без зависимостей. Каждый запрос логируется с тегами (команда, модель, cache-hit) и
стоимостью; затем агрегируем по тегам, считаем ROI автоматизации и проверяем бюджет.
Нельзя оптимизировать то, что не измеряешь.
"""


class Ledger:
    """Журнал запросов с тегами и стоимостью."""

    def __init__(self):
        self.records = []

    def record(self, cost, **tags):
        self.records.append({"cost": cost, "tags": tags})

    def total(self):
        return round(sum(r["cost"] for r in self.records), 6)

    def by_tag(self, key):
        """Суммарная стоимость в разрезе значения тега key."""
        out = {}
        for r in self.records:
            val = r["tags"].get(key, "—")
            out[val] = round(out.get(val, 0.0) + r["cost"], 6)
        return out

    def cache_hit_rate(self):
        if not self.records:
            return 0.0
        hits = sum(1 for r in self.records if r["tags"].get("cache_hit"))
        return round(hits / len(self.records), 3)

    def over_budget(self, limit):
        return self.total() > limit


def roi(before_cost, after_cost, value_gained):
    """ROI автоматизации: (выгода − затраты) / затраты. before/after — стоимость процесса."""
    saved = before_cost - after_cost
    benefit = saved + value_gained
    return round(benefit / after_cost, 2) if after_cost else float("inf")


if __name__ == "__main__":
    led = Ledger()
    led.record(0.02, team="analytics", model="sonnet-4.6", cache_hit=False)
    led.record(0.002, team="analytics", model="haiku-4.5", cache_hit=True)
    led.record(0.05, team="support", model="opus-4.8", cache_hit=False)
    print("Итого:", led.total())
    print("По командам:", led.by_tag("team"))
    print("По моделям:", led.by_tag("model"))
    print("Cache hit rate:", led.cache_hit_rate())
    print("Над бюджетом 0.05?", led.over_budget(0.05))
    print("ROI (было 100, стало 20, выгода 50):", roi(100, 20, 50))
