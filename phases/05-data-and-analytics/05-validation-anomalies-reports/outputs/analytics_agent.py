"""analytics_agent.py — артефакт урока 5.5: сквозной аналитический агент.

Самодостаточно, без зависимостей (sqlite3 + statistics из stdlib).
Пайплайн: SQL-выгрузка → валидация → поиск аномалий → markdown-отчёт.

В проде источник данных подключается через MCP-коннектор к БД (Фаза 6),
а запуск — по расписанию (cron / dbt jobs / оркестратор).

Запуск:  python analytics_agent.py
"""
import sqlite3
from statistics import mean, pstdev

# --- источник данных (в проде — реальная БД через MCP) ---
# mar — всплеск: на достаточном числе месяцев выйдет за 2σ и попадёт в аномалии.
ROWS = [
    ("Москва", "jan", 100), ("Москва", "feb", 120), ("Москва", "mar", 900),
    ("Москва", "apr", 110), ("Москва", "may", 130), ("Москва", "jun", 115),
    ("Питер", "jan", 80), ("Питер", "feb", 90), ("Питер", "mar", 85),
    ("Питер", "apr", 95), ("Питер", "may", 88), ("Питер", "jun", 92),
]


def query(sql):
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE sales (region TEXT, month TEXT, amount REAL)")
    con.executemany("INSERT INTO sales VALUES (?,?,?)", ROWS)
    result = con.execute(sql).fetchall()
    con.close()
    return result


def validate(metrics, rules):
    return [f"{k}: нарушено" for k, pred in rules.items()
            if k not in metrics or not pred(metrics[k])]


def find_anomalies(series, z=2.0):
    if len(series) < 2:
        return []
    mu, sigma = mean(series), pstdev(series)
    if sigma == 0:
        return []
    return [{"value": v, "z": round((v - mu) / sigma, 2)}
            for v in series if abs((v - mu) / sigma) > z]


def run():
    by_month = query("SELECT month, SUM(amount) FROM sales GROUP BY month")
    total = query("SELECT SUM(amount) FROM sales")[0][0]
    metrics = {"total_revenue": total, "months": len(by_month)}

    problems = validate(metrics, {"total_revenue": lambda x: x >= 0,
                                  "months": lambda x: x > 0})
    anomalies = find_anomalies([v for _, v in by_month])

    lines = ["# Авто-отчёт по выручке", "", "## Метрики",
             f"- Итого выручка: {total}", f"- Месяцев: {len(by_month)}",
             "", "## По месяцам"]
    lines += [f"- {m}: {v}" for m, v in by_month]
    lines += ["", "## Контроль качества"]
    lines.append(f"- Валидация: {'OK' if not problems else problems}")
    lines.append(f"- Аномалии: {anomalies or 'не обнаружено'}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(run())
