from monitoring import CallLogger


def _log():
    log = CallLogger()
    for ms, ok in [(120, True), (300, True), (90, True), (1500, False), (200, True)]:
        log.log("sonnet-4.6", ms, ok=ok, error=None if ok else "timeout")
    return log


def test_error_rate():
    assert _log().error_rate() == 0.2          # 1 из 5


def test_latency_percentile_returns_high_value():
    p95 = _log().latency_percentile(95)
    assert p95 == 1500                          # худшая латентность в хвосте


def test_recent_errors_captured():
    errs = _log().recent_errors()
    assert len(errs) == 1
    assert errs[0]["error"] == "timeout"


def test_empty_logger_safe():
    log = CallLogger()
    assert log.error_rate() == 0.0
    assert log.latency_percentile() == 0.0
