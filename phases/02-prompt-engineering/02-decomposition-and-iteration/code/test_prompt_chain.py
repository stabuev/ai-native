from prompt_chain import ChainStep, run_chain, DEMO_CHAIN


def test_chain_composes_steps():
    answer, history = run_chain(DEMO_CHAIN, "взял 2 и 3 и 5")
    assert answer == "Итого: 10"
    assert len(history) == 3
    assert [h["step"] for h in history] == ["extract", "sum", "format"]


def test_history_records_in_and_out():
    _, history = run_chain(DEMO_CHAIN, "1 и 4")
    assert history[0]["in"] == "1 и 4"
    assert history[-1]["out"] == "Итого: 5"


def test_single_step_cannot_solve_what_chain_solves():
    # один «extract» не доводит до финальной строки — нужна вся цепочка
    extract_only, _ = run_chain([DEMO_CHAIN[0]], "2 и 3")
    assert extract_only == [2, 3]
    full, _ = run_chain(DEMO_CHAIN, "2 и 3")
    assert full == "Итого: 5"


def test_custom_chain():
    steps = [ChainStep("upper", str.upper), ChainStep("bang", lambda s: s + "!")]
    out, _ = run_chain(steps, "ok")
    assert out == "OK!"
