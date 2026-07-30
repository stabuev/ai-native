from copy import deepcopy

import pytest

from analyze import (
    CSV_DEMO,
    DEMO_PLAN,
    PlanError,
    execute_plan,
    load_csv,
)


ROWS = load_csv(CSV_DEMO)


def test_load_csv_preserves_rows_and_declared_columns():
    assert len(ROWS) == 6
    assert ROWS[0]["order_id"] == "o-1"
    assert ROWS[0]["amount"] == "100"


def test_sum_and_count_plans_filter_period_and_status_before_grouping():
    result = execute_plan(ROWS, DEMO_PLAN)

    assert result["rows_read"] == 6
    assert result["rows_used"] == 4
    assert result["rows_excluded"] == 2
    assert result["groups"] == [
        {"group": "Москва", "value": 150.0, "rows": 2},
        {"group": "Питер", "value": 30.0, "rows": 1},
        {"group": "Казань", "value": 20.0, "rows": 1},
    ]
    assert result["overall"] == 200.0

    count_plan = deepcopy(DEMO_PLAN)
    count_plan["metric"] = {
        "name": "paid_orders",
        "column": "order_id",
        "aggregation": "count_rows",
        "unit": "orders",
    }
    count_result = execute_plan(ROWS, count_plan)
    assert count_result["overall"] == 4
    assert count_result["groups"][0] == {
        "group": "Москва",
        "value": 2,
        "rows": 2,
    }
    assert count_result["checks"]["reconciled"] is True


def test_top_n_keeps_other_value_and_reconciles_against_full_result():
    result = execute_plan(ROWS, DEMO_PLAN)

    assert [item["group"] for item in result["top"]] == ["Москва", "Питер"]
    assert sum(item["value"] for item in result["top"]) == 180.0
    assert result["other_value"] == 20.0
    assert result["checks"]["reconciled"] is True


def test_mean_uses_weighted_reconciliation_not_sum_of_group_means():
    plan = deepcopy(DEMO_PLAN)
    plan["metric"] = {
        "name": "average_paid_order",
        "column": "amount",
        "aggregation": "mean",
        "unit": "RUB/order",
    }

    result = execute_plan(ROWS, plan)

    assert result["groups"][0] == {
        "group": "Москва",
        "value": 75.0,
        "rows": 2,
    }
    assert result["overall"] == 50.0
    assert result["other_value"] is None
    assert result["checks"]["reconciled"] is True


def test_unknown_aggregation_is_rejected_instead_of_becoming_sum():
    plan = deepcopy(DEMO_PLAN)
    plan["metric"]["aggregation"] = "median"

    with pytest.raises(PlanError, match="aggregation"):
        execute_plan(ROWS, plan)


def test_non_numeric_metric_value_is_visible_instead_of_becoming_zero():
    broken_rows = deepcopy(ROWS)
    broken_rows[0]["amount"] = "unknown"

    with pytest.raises(PlanError, match="non-numeric"):
        execute_plan(broken_rows, DEMO_PLAN)


def test_duplicate_row_id_blocks_a_broken_grain():
    duplicated = [*deepcopy(ROWS), deepcopy(ROWS[0])]

    with pytest.raises(PlanError, match="duplicate row ids"):
        execute_plan(duplicated, DEMO_PLAN)


def test_missing_column_or_empty_filter_result_blocks_execution():
    missing_column_plan = deepcopy(DEMO_PLAN)
    missing_column_plan["group_by"] = "city"
    with pytest.raises(PlanError, match="columns missing"):
        execute_plan(ROWS, missing_column_plan)

    empty_plan = deepcopy(DEMO_PLAN)
    empty_plan["filters"]["quarter"] = "Q9"
    with pytest.raises(PlanError, match="no rows match"):
        execute_plan(ROWS, empty_plan)
