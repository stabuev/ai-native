"""Презентация и защита: метрики «до/после» + ROI — Build It для урока 12.3.

Без зависимостей. Защита Capstone строится на цифрах: насколько упало время и
стоимость, насколько выросло качество, какой ROI. Здесь считаем улучшения,
окупаемость и собираем сводку для презентации.
"""


def improvement(before, after, lower_is_better=True):
    """% улучшения. lower_is_better=True для времени/стоимости (меньше = лучше)."""
    if before == 0:
        return 0.0
    delta = (before - after) / before if lower_is_better else (after - before) / before
    return round(delta * 100, 1)


def roi(before_cost, after_cost, value_gained=0.0):
    """ROI автоматизации: (экономия + выгода) / затраты."""
    saved = before_cost - after_cost
    return round((saved + value_gained) / after_cost, 2) if after_cost else float("inf")


def before_after(before, after, lower_is_better):
    """before/after: dict метрика→значение. lower_is_better: dict метрика→bool."""
    return {
        k: {"before": before[k], "after": after[k],
            "improvement_pct": improvement(before[k], after[k], lower_is_better.get(k, True))}
        for k in before
    }


def competency_report(checked):
    """checked: dict компетенция→bool. Возвращает сводку готовности."""
    done = sum(1 for v in checked.values() if v)
    return {"done": done, "total": len(checked),
            "missing": [k for k, v in checked.items() if not v]}


if __name__ == "__main__":
    before = {"время_мин": 10.0, "стоимость_$": 0.50, "качество_%": 70.0}
    after = {"время_мин": 3.0, "стоимость_$": 0.10, "качество_%": 88.0}
    lower = {"время_мин": True, "стоимость_$": True, "качество_%": False}
    for k, v in before_after(before, after, lower).items():
        print(f"{k}: {v['before']} → {v['after']} ({v['improvement_pct']:+.1f}%)")
    print("ROI:", roi(before_cost=1000, after_cost=200, value_gained=300))
