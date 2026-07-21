from tracer import Tracer


def _fake_clock(values):
    it = iter(values)
    return lambda: next(it)


def test_nested_spans_and_parent():
    # последовательность вызовов часов: a.start, b.start, b.end, a.end
    tr = Tracer(clock=_fake_clock([0, 1, 3, 6]))
    with tr.span("a"):
        with tr.span("b"):
            pass
    by_name = {s["name"]: s for s in tr.spans}
    assert by_name["b"]["parent"] == "a"
    assert by_name["a"]["parent"] is None
    assert by_name["b"]["duration"] == 2
    assert by_name["a"]["duration"] == 6


def test_total_duration_counts_roots():
    tr = Tracer(clock=_fake_clock([0, 1, 3, 6]))
    with tr.span("a"):
        with tr.span("b"):
            pass
    assert tr.total_duration() == 6        # только корневой span


def test_slowest_span():
    tr = Tracer(clock=_fake_clock([0, 1, 3, 6]))
    with tr.span("a"):
        with tr.span("b"):
            pass
    assert tr.slowest()["name"] == "a"


def test_attributes_recorded():
    tr = Tracer(clock=_fake_clock([0, 1]))
    with tr.span("llm", model="sonnet-4.6"):
        pass
    assert tr.spans[0]["attrs"]["model"] == "sonnet-4.6"
