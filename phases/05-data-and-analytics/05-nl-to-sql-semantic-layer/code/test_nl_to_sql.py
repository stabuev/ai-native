import pytest
from nl_to_sql import nl_to_sql, run_sql, DEMO_ROWS


def test_metric_with_dimension_makes_group_by():
    assert nl_to_sql("выручка по регионам") == \
        "SELECT region, SUM(amount) FROM sales GROUP BY region"


def test_metric_without_dimension():
    assert nl_to_sql("сколько всего заказов") == "SELECT COUNT(*) FROM sales"


def test_avg_metric():
    assert nl_to_sql("какой средний чек по месяцам") == \
        "SELECT month, AVG(amount) FROM sales GROUP BY month"


def test_unknown_metric_raises():
    with pytest.raises(ValueError):
        nl_to_sql("какая погода завтра")


def test_run_sql_executes_aggregation():
    sql = nl_to_sql("выручка по регионам")
    result = dict(run_sql(sql, DEMO_ROWS))
    assert result["Москва"] == 150
    assert result["Питер"] == 100
