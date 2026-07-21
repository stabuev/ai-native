"""NL→SQL + семантический слой — Build It для урока 5.3.

Без внешних зависимостей (sqlite3 из stdlib). Семантический слой описывает метрики
и измерения в терминах бизнеса; наивный NL→SQL по ключевым словам собирает запрос
и исполняет его на sqlite. В USE IT разбор естественного языка делает LLM, но
семантический слой (определения метрик) остаётся — он гарантирует единый смысл.
"""
import sqlite3

SEMANTIC = {
    "table": "sales",
    "metrics": {                        # ключ — стем-триггер (подстрока в вопросе)
        "средний чек": "AVG(amount)",   # порядок важен: более специфичные — выше
        "выручк": "SUM(amount)",
        "заказ": "COUNT(*)",
    },
    "dimensions": {"регион": "region", "месяц": "month"},
}


def nl_to_sql(question, semantic=SEMANTIC):
    """Собрать SQL по вопросу: найти метрику и (опц.) измерение для GROUP BY."""
    q = question.lower()
    metric_sql = next((sql for name, sql in semantic["metrics"].items() if name in q), None)
    if metric_sql is None:
        raise ValueError("не нашёл метрику в вопросе")
    dim_col = next((col for name, col in semantic["dimensions"].items() if name in q), None)
    table = semantic["table"]
    if dim_col:
        return f"SELECT {dim_col}, {metric_sql} FROM {table} GROUP BY {dim_col}"
    return f"SELECT {metric_sql} FROM {table}"


def run_sql(sql, rows):
    """Создать in-memory таблицу sales(region, month, amount) и выполнить SQL."""
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE sales (region TEXT, month TEXT, amount REAL)")
    con.executemany("INSERT INTO sales VALUES (?,?,?)", rows)
    result = con.execute(sql).fetchall()
    con.close()
    return result


DEMO_ROWS = [
    ("Москва", "jan", 100), ("Москва", "feb", 50),
    ("Питер", "jan", 30), ("Питер", "feb", 70), ("Казань", "jan", 20),
]

if __name__ == "__main__":
    for q in ["выручка по регионам", "сколько заказов", "средний чек"]:
        sql = nl_to_sql(q)
        print(f"{q!r}\n  SQL: {sql}\n  ->  {run_sql(sql, DEMO_ROWS)}")
