"""Минимальный semantic contract и детерминированный intent→SQL-компилятор.

Естественный язык здесь намеренно не разбирается самодельными правилами. Модель или
человек предлагают структурированный intent, а этот модуль проверяет его по разрешённым
метрикам, измерениям и фильтрам, компилирует SQL и исполняет его на учебной SQLite.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping, Sequence
from typing import Any


SEMANTIC = {
    "version": "1.0",
    "owner": "course-team",
    "table": "sales",
    "grain": "одна строка = один заказ",
    "metrics": {
        "paid_revenue": {
            "label": "Оплаченная выручка",
            "expression": "SUM(amount)",
            "unit": "RUB",
            "required_filters": {"status": "paid"},
        },
        "paid_orders": {
            "label": "Число оплаченных заказов",
            "expression": "COUNT(*)",
            "unit": "orders",
            "required_filters": {"status": "paid"},
        },
    },
    "dimensions": {
        "region": {"label": "Регион", "column": "region"},
        "quarter": {"label": "Квартал", "column": "quarter"},
    },
    "filters": {
        "quarter": {"column": "quarter"},
        "status": {"column": "status"},
    },
}


DEMO_ROWS = [
    ("o-1", "Q2", "Москва", "paid", 100.0),
    ("o-2", "Q2", "Москва", "paid", 50.0),
    ("o-3", "Q2", "Питер", "paid", 30.0),
    ("o-4", "Q2", "Питер", "refunded", 70.0),
    ("o-5", "Q2", "Казань", "paid", 20.0),
    ("o-6", "Q1", "Москва", "paid", 999.0),
]


def compile_query(
    intent: Mapping[str, Any],
    semantic: Mapping[str, Any] = SEMANTIC,
) -> dict[str, Any]:
    """Проверить intent и собрать SELECT с параметрами.

    Ожидаемая форма:
    {
        "metric": "paid_revenue",
        "dimensions": ["region"],
        "filters": {"quarter": "Q2"},
    }
    """

    if not isinstance(intent, Mapping):
        raise ValueError("intent должен быть объектом")

    allowed_fields = {"metric", "dimensions", "filters"}
    unknown_fields = set(intent) - allowed_fields
    if unknown_fields:
        names = ", ".join(sorted(unknown_fields))
        raise ValueError(f"неизвестные поля intent: {names}")

    metric_id = intent.get("metric")
    metric_spec = semantic["metrics"].get(metric_id)
    if metric_spec is None:
        raise ValueError(f"неизвестная метрика: {metric_id!r}")

    dimension_ids = intent.get("dimensions", [])
    if (
        not isinstance(dimension_ids, Sequence)
        or isinstance(dimension_ids, (str, bytes))
    ):
        raise ValueError("dimensions должен быть списком")
    if any(not isinstance(dimension_id, str) for dimension_id in dimension_ids):
        raise ValueError("каждое измерение должно быть строковым ID")
    if len(set(dimension_ids)) != len(dimension_ids):
        raise ValueError("dimensions не должен содержать повторы")

    dimension_columns = []
    for dimension_id in dimension_ids:
        dimension_spec = semantic["dimensions"].get(dimension_id)
        if dimension_spec is None:
            raise ValueError(f"неизвестное измерение: {dimension_id!r}")
        dimension_columns.append(dimension_spec["column"])

    requested_filters = intent.get("filters", {})
    if not isinstance(requested_filters, Mapping):
        raise ValueError("filters должен быть объектом")

    effective_filters = dict(metric_spec.get("required_filters", {}))
    for filter_id, value in requested_filters.items():
        if filter_id not in semantic["filters"]:
            raise ValueError(f"неизвестный фильтр: {filter_id!r}")
        if filter_id in effective_filters and effective_filters[filter_id] != value:
            required = effective_filters[filter_id]
            raise ValueError(
                f"метрика {metric_id!r} требует {filter_id}={required!r}"
            )
        if not isinstance(value, (str, int, float)):
            raise ValueError(f"неподдерживаемое значение фильтра: {filter_id!r}")
        effective_filters[filter_id] = value

    select_parts = [
        *dimension_columns,
        f'{metric_spec["expression"]} AS {metric_id}',
    ]
    sql = f'SELECT {", ".join(select_parts)} FROM {semantic["table"]}'

    clauses = []
    params = []
    for filter_id, filter_spec in semantic["filters"].items():
        if filter_id in effective_filters:
            clauses.append(f'{filter_spec["column"]} = ?')
            params.append(effective_filters[filter_id])
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    if dimension_columns:
        joined = ", ".join(dimension_columns)
        sql += f" GROUP BY {joined} ORDER BY {joined}"

    return {
        "sql": sql,
        "params": tuple(params),
        "metric": metric_id,
        "dimensions": list(dimension_ids),
        "filters": effective_filters,
        "unit": metric_spec["unit"],
        "semantic_version": semantic["version"],
    }


def run_read_only(
    compiled: Mapping[str, Any],
    rows: Sequence[tuple[Any, ...]] = DEMO_ROWS,
) -> list[dict[str, Any]]:
    """Исполнить один SELECT на учебной SQLite и вернуть именованные строки."""

    sql = str(compiled.get("sql", "")).strip()
    if not sql.upper().startswith("SELECT ") or ";" in sql:
        raise ValueError("разрешён только один SELECT без точки с запятой")

    connection = sqlite3.connect(":memory:")
    try:
        connection.execute(
            """
            CREATE TABLE sales (
                order_id TEXT PRIMARY KEY,
                quarter TEXT NOT NULL,
                region TEXT NOT NULL,
                status TEXT NOT NULL,
                amount REAL NOT NULL
            )
            """
        )
        connection.executemany(
            "INSERT INTO sales VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        connection.execute("PRAGMA query_only = ON")
        cursor = connection.execute(sql, tuple(compiled.get("params", ())))
        columns = [item[0] for item in cursor.description]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
    finally:
        connection.close()


def reconcile_total(
    compiled: Mapping[str, Any],
    result: Sequence[Mapping[str, Any]],
    expected_total: float,
) -> dict[str, Any]:
    """Сверить сумму групп с заранее ожидаемым полным итогом."""

    metric_id = compiled["metric"]
    actual_total = sum(float(row[metric_id]) for row in result)
    return {
        "metric": metric_id,
        "expected_total": float(expected_total),
        "actual_total": actual_total,
        "matches": abs(actual_total - float(expected_total)) < 1e-9,
    }


if __name__ == "__main__":
    demo_intent = {
        "metric": "paid_revenue",
        "dimensions": ["region"],
        "filters": {"quarter": "Q2"},
    }
    demo_query = compile_query(demo_intent)
    demo_result = run_read_only(demo_query)
    demo_check = reconcile_total(demo_query, demo_result, expected_total=200)

    print("intent:", demo_intent)
    print("semantic_version:", demo_query["semantic_version"])
    print("sql:", demo_query["sql"])
    print("params:", demo_query["params"])
    print("result:", demo_result)
    print("reconciliation:", demo_check)
