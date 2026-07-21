import pytest
from orchestrator import Orchestrator


def _orch():
    o = Orchestrator()
    o.register("researcher", lambda topic: [f"факт:{topic}"])
    o.register("writer", lambda ctx: f"черновик({len(ctx['facts'])})")
    return o


def test_delegate_routes_to_role():
    assert _orch().delegate("researcher", "X") == ["факт:X"]


def test_unknown_role_raises():
    with pytest.raises(KeyError):
        _orch().delegate("designer", "X")


def test_run_collects_results_by_role():
    o = _orch()
    facts = o.delegate("researcher", "RAG")
    results = o.run([("writer", {"facts": facts})])
    assert results["writer"] == "черновик(1)"


def test_pipeline_passes_results_forward():
    o = _orch()
    facts = o.delegate("researcher", "тема")
    results = o.run([("writer", {"facts": facts})])
    assert "черновик" in results["writer"]
