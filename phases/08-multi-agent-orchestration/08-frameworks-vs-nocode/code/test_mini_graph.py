from mini_graph import Graph, END


def test_linear_graph():
    g = Graph()
    g.add_node("a", lambda s: {**s, "log": s["log"] + ["a"]})
    g.add_node("b", lambda s: {**s, "log": s["log"] + ["b"]})
    g.set_entry("a")
    g.add_edge("a", "b")
    g.add_edge("b", END)
    state, path = g.run({"log": []})
    assert path == ["a", "b"]
    assert state["log"] == ["a", "b"]


def test_conditional_branch():
    g = Graph()
    g.add_node("check", lambda s: s)
    g.add_node("big", lambda s: {**s, "label": "big"})
    g.add_node("small", lambda s: {**s, "label": "small"})
    g.set_entry("check")
    g.add_conditional("check", lambda s: "big" if s["x"] > 10 else "small")
    g.add_edge("big", END)
    g.add_edge("small", END)
    assert g.run({"x": 42})[0]["label"] == "big"
    assert g.run({"x": 3})[0]["label"] == "small"


def test_loop_with_exit():
    g = Graph()
    g.add_node("inc", lambda s: {**s, "n": s["n"] + 1})
    g.set_entry("inc")
    g.add_conditional("inc", lambda s: "inc" if s["n"] < 3 else END)
    state, path = g.run({"n": 0})
    assert state["n"] == 3
    assert path == ["inc", "inc", "inc"]


def test_max_steps_guard():
    g = Graph()
    g.add_node("loop", lambda s: s)
    g.set_entry("loop")
    g.add_conditional("loop", lambda s: "loop")     # бесконечный цикл
    _, path = g.run({}, max_steps=5)
    assert len(path) == 5                            # лимит сработал
