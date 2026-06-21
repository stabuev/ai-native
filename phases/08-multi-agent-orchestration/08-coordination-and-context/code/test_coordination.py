from coordination import SharedContext, run_process


def test_write_read():
    ctx = SharedContext()
    ctx.write("k", 1, "a")
    assert ctx.read("k") == 1
    assert ctx.read("missing", "def") == "def"


def test_conflict_detected_on_cross_agent_overwrite():
    ctx = SharedContext()
    ctx.write("facts", ["A"], "agent1")
    ctx.write("facts", ["X"], "agent2")          # другой агент, другое значение
    assert len(ctx.conflicts) == 1
    assert ctx.conflicts[0]["by"] == "agent2" and ctx.conflicts[0]["prev_by"] == "agent1"


def test_no_conflict_same_agent_or_same_value():
    ctx = SharedContext()
    ctx.write("k", 1, "a")
    ctx.write("k", 2, "a")                        # тот же агент → не конфликт
    ctx.write("k", 2, "b")                        # другой агент, но то же значение → не конфликт
    assert ctx.conflicts == []


def test_process_passes_context_between_agents():
    def producer(ctx, me):
        ctx.write("facts", ["A", "B"], me)

    def consumer(ctx, me):
        ctx.write("draft", len(ctx.read("facts")), me)

    ctx = run_process([("producer", producer), ("consumer", consumer)])
    assert ctx.read("draft") == 2                 # consumer увидел контекст producer'а
    assert ctx.conflicts == []
