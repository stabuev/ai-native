import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bi_investigation_flows_into_validation_gate():
    bi_agent = _load_module(
        "phase5_bi_agent",
        ROOT / "phases/05-data-and-analytics/04-bi-agents/code/bi_agent.py",
    )
    validation = _load_module(
        "phase5_validation",
        ROOT
        / "phases/05-data-and-analytics/05-validation-anomalies-reports/code/validation.py",
    )

    investigation = bi_agent.investigate(
        "Почему paid_revenue снизилась в Q2 относительно Q1?"
    )
    packet = validation.build_validation_packet(
        investigation,
        bi_agent.SEMANTIC,
        run_id="phase-5-integration-test",
        as_of="2026-07-01",
        history=validation.DEMO_PACKET["history"],
    )
    result = validation.run_quality_gate(packet)

    assert investigation["status"] == "ready_for_review"
    assert len(investigation["trace"]) == 3
    assert set(packet["breakdowns"]) == {"region", "product|region=Питер"}
    assert result["decision"] == "publish"
    assert not [check for check in result["checks"] if not check["passed"]]
