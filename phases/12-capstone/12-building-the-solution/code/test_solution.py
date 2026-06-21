import pytest
from solution import Capstone, classify


def test_classify_routes_by_complexity():
    assert classify("сделай саммари") == "low"
    assert classify("проведи анализ кода") == "high"


def test_run_routes_cheap_for_simple():
    res = Capstone().run("переведи фразу")
    assert res["model"] == "haiku-4.5"
    assert res["level"] == "low"


def test_run_routes_top_for_complex():
    res = Capstone().run("сложный анализ архитектуры")
    assert res["model"] == "opus-4.8"


def test_memory_and_telemetry_recorded():
    cap = Capstone()
    cap.run("задача один")
    cap.run("анализ задачи два")
    assert len(cap.memory) == 2
    assert len(cap.telemetry) == 2
    assert cap.total_cost() > 0


def test_empty_task_blocked_by_guardrail():
    with pytest.raises(ValueError):
        Capstone().run("   ")
