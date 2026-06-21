"""Валидация, аномалии, автоотчёты — Build It для урока 5.5.

Без внешних зависимостей (statistics из stdlib). Проверяем результат на
вменяемость, ищем аномалии (z-score), собираем markdown-отчёт. Это контроль
качества аналитики перед показом цифр (мост к Фазе 11 — фактчекинг).
"""
from statistics import mean, pstdev


def validate_result(metrics, rules):
    """metrics: dict; rules: {key: predicate(value)->bool}. Список нарушений."""
    problems = []
    for key, predicate in rules.items():
        if key not in metrics:
            problems.append(f"{key}: отсутствует")
        elif not predicate(metrics[key]):
            problems.append(f"{key}: не прошёл проверку (={metrics[key]})")
    return problems


def find_anomalies(series, z=2.0):
    """Значения, отклоняющиеся больше чем на z стандартных отклонений (z-score)."""
    if len(series) < 2:
        return []
    mu, sigma = mean(series), pstdev(series)
    if sigma == 0:
        return []
    return [{"index": i, "value": v, "z": round((v - mu) / sigma, 2)}
            for i, v in enumerate(series) if abs((v - mu) / sigma) > z]


def build_report(title, metrics, anomalies):
    """Собрать markdown-отчёт из метрик и найденных аномалий."""
    lines = [f"# {title}", "", "## Метрики"]
    lines += [f"- {k}: {v}" for k, v in metrics.items()]
    lines += ["", "## Аномалии"]
    if anomalies:
        lines += [f"- индекс {a['index']}: {a['value']} (z={a['z']})" for a in anomalies]
    else:
        lines.append("- не обнаружено")
    return "\n".join(lines)


if __name__ == "__main__":
    metrics = {"revenue": 270.0, "orders": 5, "avg_check": 54.0}
    rules = {"revenue": lambda x: x >= 0, "orders": lambda x: x > 0}
    print("Нарушения:", validate_result(metrics, rules) or "нет")
    series = [100, 110, 95, 105, 100, 500]      # 500 — выброс
    anomalies = find_anomalies(series)
    print(build_report("Дневной отчёт", metrics, anomalies))
