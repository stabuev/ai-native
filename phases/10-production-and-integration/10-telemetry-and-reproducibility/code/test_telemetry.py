from telemetry import Telemetry, RunConfig


def _tel():
    t = Telemetry()
    t.record("summarize", 1000, 200, 0.005)
    t.record("summarize", 800, 150, 0.004)
    t.record("classify", 300, 10, 0.0003)
    return t


def test_aggregation_by_process():
    by = _tel().by_process()
    assert by["summarize"]["tokens_in"] == 1800
    assert by["summarize"]["cost"] == 0.009
    assert by["classify"]["tokens_out"] == 10


def test_total_cost():
    assert _tel().total_cost() == 0.0093


def test_fingerprint_is_deterministic():
    assert RunConfig("sonnet-4.6").fingerprint() == RunConfig("sonnet-4.6").fingerprint()


def test_fingerprint_changes_with_params():
    a = RunConfig("sonnet-4.6", temperature=0.0)
    b = RunConfig("sonnet-4.6", temperature=0.7)
    assert a.fingerprint() != b.fingerprint()
    # другая версия промпта тоже меняет отпечаток
    assert a.fingerprint() != RunConfig("sonnet-4.6", prompt_version="v2").fingerprint()
