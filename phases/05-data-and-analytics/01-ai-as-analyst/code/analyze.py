"""Проверяемый исполнитель простого аналитического плана для урока 5.1.

Модуль не понимает естественный язык и не изображает ИИ. Человек или модель сначала
предлагает AnalysisPlan, человек проверяет определения, а этот код детерминированно
валидирует и исполняет простую групповую агрегацию над CSV.
"""

import csv
import io
from math import isclose


ALLOWED_AGGREGATIONS = {"sum", "mean", "count_rows"}
REQUIRED_PLAN_FIELDS = {
    "question",
    "source",
    "grain",
    "row_id",
    "period",
    "filters",
    "metric",
    "group_by",
    "top_n",
}


class PlanError(ValueError):
    """План или данные не позволяют получить проверяемый результат."""


def load_csv(text):
    """Прочитать непустой CSV-текст в список строк-словарей."""
    reader = csv.DictReader(io.StringIO(text.strip()))
    if not reader.fieldnames:
        raise PlanError("CSV must contain a header")
    rows = list(reader)
    if not rows:
        raise PlanError("CSV must contain at least one data row")
    return rows


def validate_plan(rows, plan):
    """Проверить контракт плана, колонки и заявленный grain до расчёта."""
    if not isinstance(plan, dict):
        raise PlanError("plan must be a mapping")
    missing_fields = sorted(REQUIRED_PLAN_FIELDS - set(plan))
    if missing_fields:
        raise PlanError(f"plan fields missing: {', '.join(missing_fields)}")

    for field in ("question", "source", "grain", "row_id", "period", "group_by"):
        value = plan[field]
        if not isinstance(value, str) or not value.strip():
            raise PlanError(f"plan.{field} must be a non-empty string")

    filters = plan["filters"]
    if not isinstance(filters, dict):
        raise PlanError("plan.filters must be a mapping")

    metric = plan["metric"]
    if not isinstance(metric, dict):
        raise PlanError("plan.metric must be a mapping")
    for field in ("name", "column", "aggregation", "unit"):
        value = metric.get(field)
        if not isinstance(value, str) or not value.strip():
            raise PlanError(f"plan.metric.{field} must be a non-empty string")
    if metric["aggregation"] not in ALLOWED_AGGREGATIONS:
        raise PlanError(
            "plan.metric.aggregation must be one of "
            + ", ".join(sorted(ALLOWED_AGGREGATIONS))
        )

    top_n = plan["top_n"]
    if not isinstance(top_n, int) or isinstance(top_n, bool) or top_n <= 0:
        raise PlanError("plan.top_n must be a positive integer")

    columns = set(rows[0])
    required_columns = {
        plan["row_id"],
        plan["group_by"],
        *filters.keys(),
        metric["column"],
    }
    missing_columns = sorted(required_columns - columns)
    if missing_columns:
        raise PlanError(f"data columns missing: {', '.join(missing_columns)}")

    row_ids = [row.get(plan["row_id"]) for row in rows]
    if any(row_id in (None, "") for row_id in row_ids):
        raise PlanError("row_id contains an empty value")
    if len(row_ids) != len(set(row_ids)):
        raise PlanError("duplicate row ids violate the declared grain")


def _number(value, *, row_id, column):
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise PlanError(
            f"row {row_id} contains a non-numeric value in {column}"
        ) from exc


def execute_plan(rows, plan):
    """Исполнить проверенную групповую агрегацию и вернуть расчёт с проверками."""
    validate_plan(rows, plan)

    filters = plan["filters"]
    selected = [
        row
        for row in rows
        if all(row.get(column) == expected for column, expected in filters.items())
    ]
    if not selected:
        raise PlanError("no rows match the declared filters")

    metric = plan["metric"]
    aggregation = metric["aggregation"]
    metric_column = metric["column"]
    row_id_column = plan["row_id"]
    group_column = plan["group_by"]
    groups = {}

    for row in selected:
        group = row.get(group_column)
        if group in (None, ""):
            raise PlanError(f"row {row[row_id_column]} has an empty group")
        bucket = groups.setdefault(group, {"rows": 0, "values": []})
        bucket["rows"] += 1
        if aggregation != "count_rows":
            bucket["values"].append(
                _number(
                    row.get(metric_column),
                    row_id=row[row_id_column],
                    column=metric_column,
                )
            )

    group_results = []
    all_values = []
    for group, bucket in groups.items():
        values = bucket["values"]
        if aggregation == "count_rows":
            value = bucket["rows"]
        elif aggregation == "sum":
            value = sum(values)
            all_values.extend(values)
        else:
            value = sum(values) / len(values)
            all_values.extend(values)
        group_results.append(
            {"group": group, "value": value, "rows": bucket["rows"]}
        )

    group_results.sort(key=lambda item: (-item["value"], str(item["group"])))
    top = group_results[: plan["top_n"]]

    if aggregation == "count_rows":
        overall = len(selected)
        reconciled = sum(item["value"] for item in group_results) == overall
        other_value = overall - sum(item["value"] for item in top)
        reconciliation_rule = "sum of all group counts equals selected row count"
    elif aggregation == "sum":
        overall = sum(all_values)
        reconciled = isclose(
            sum(item["value"] for item in group_results),
            overall,
            rel_tol=1e-12,
            abs_tol=1e-12,
        )
        other_value = overall - sum(item["value"] for item in top)
        reconciliation_rule = "sum of all group values equals overall sum"
    else:
        overall = sum(all_values) / len(all_values)
        weighted = sum(item["value"] * item["rows"] for item in group_results)
        reconciled = isclose(
            weighted / len(selected),
            overall,
            rel_tol=1e-12,
            abs_tol=1e-12,
        )
        other_value = None
        reconciliation_rule = "weighted group mean equals overall mean"

    return {
        "question": plan["question"],
        "metric": metric["name"],
        "unit": metric["unit"],
        "rows_read": len(rows),
        "rows_used": len(selected),
        "rows_excluded": len(rows) - len(selected),
        "groups": group_results,
        "top": top,
        "overall": overall,
        "other_value": other_value,
        "checks": {
            "row_ids_unique": True,
            "required_values_valid": True,
            "reconciled": reconciled,
            "reconciliation_rule": reconciliation_rule,
        },
    }


CSV_DEMO = """order_id,quarter,region,status,amount
o-1,Q2,Москва,paid,100
o-2,Q2,Москва,paid,50
o-3,Q2,Питер,paid,30
o-4,Q2,Питер,refunded,70
o-5,Q2,Казань,paid,20
o-6,Q1,Москва,paid,999
"""

DEMO_PLAN = {
    "question": "Какие регионы принесли больше оплаченной выручки в Q2?",
    "source": "sales.csv",
    "grain": "одна строка = один заказ",
    "row_id": "order_id",
    "period": "Q2",
    "filters": {"quarter": "Q2", "status": "paid"},
    "metric": {
        "name": "paid_revenue",
        "column": "amount",
        "aggregation": "sum",
        "unit": "RUB",
    },
    "group_by": "region",
    "top_n": 2,
}


if __name__ == "__main__":
    report = execute_plan(load_csv(CSV_DEMO), DEMO_PLAN)
    print("Строк прочитано / использовано:", report["rows_read"], "/", report["rows_used"])
    print("Все группы:", report["groups"])
    print("Топ-2:", report["top"], "Остальные:", report["other_value"])
    print("Общий итог:", report["overall"])
    print("Проверки:", report["checks"])
