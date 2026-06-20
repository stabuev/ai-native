from context_engine import estimate_tokens, assemble, compact_history


def _layers():
    w = lambda n: " ".join(["w"] * n)
    return [
        {"name": "system", "content": w(20), "priority": 4},
        {"name": "rag", "content": w(30), "priority": 3},
        {"name": "memory", "content": w(20), "priority": 2},
        {"name": "history", "content": w(40), "priority": 1},
    ]


def test_estimate_tokens_counts_words():
    assert estimate_tokens("раз два три") == 3


def test_assemble_keeps_all_when_fits():
    res = assemble(_layers(), budget=1000)
    assert {l["name"] for l in res["kept"]} == {"system", "rag", "memory", "history"}
    assert res["dropped"] == []


def test_assemble_drops_low_priority_to_fit():
    res = assemble(_layers(), budget=60)        # system(20)+rag(30)+memory? 50+20=70>60
    kept = {l["name"] for l in res["kept"]}
    assert "system" in kept and "rag" in kept   # высокий приоритет сохранён
    assert "history" not in kept                # самый низкий отброшен
    assert res["tokens"] <= 60


def test_assemble_respects_priority_order():
    # бюджета хватает только на самый важный слой
    res = assemble(_layers(), budget=20)
    assert [l["name"] for l in res["kept"]] == ["system"]


def test_compact_history_keeps_recent():
    assert compact_history(["m1", "m2", "m3", "m4"], 2) == ["m3", "m4"]
    assert compact_history(["m1"], 5) == ["m1"]
