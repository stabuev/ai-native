from validation import validate_result, find_anomalies, build_report


def test_validate_flags_failing_and_missing():
    metrics = {"revenue": -5}
    problems = validate_result(metrics, {"revenue": lambda x: x >= 0, "orders": lambda x: x > 0})
    assert any("revenue" in p for p in problems)
    assert any("orders" in p and "отсутствует" in p for p in problems)


def test_validate_passes_good_metrics():
    metrics = {"revenue": 270, "orders": 5}
    assert validate_result(metrics, {"revenue": lambda x: x >= 0, "orders": lambda x: x > 0}) == []


def test_find_anomalies_flags_outlier():
    anomalies = find_anomalies([100, 110, 95, 105, 100, 500])
    assert len(anomalies) == 1
    assert anomalies[0]["value"] == 500


def test_no_anomalies_when_uniform():
    assert find_anomalies([5, 5, 5, 5]) == []
    assert find_anomalies([42]) == []


def test_report_contains_metrics_and_anomalies():
    report = build_report("Отчёт", {"revenue": 270}, [{"index": 5, "value": 500, "z": 2.2}])
    assert "# Отчёт" in report
    assert "revenue: 270" in report
    assert "индекс 5" in report
