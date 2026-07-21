from project import Project

KB = [
    "Возврат товара возможен в течение 14 дней.",
    "Гарантия на электронику составляет 12 месяцев.",
    "Доставка по городу занимает 1-2 дня.",
]


def _proj():
    return Project("support", "Ты ассистент поддержки.", KB)


def test_context_includes_system_prompt_and_query():
    ctx = _proj().build_context("вопрос про возврат")
    assert "Ты ассистент поддержки." in ctx
    assert "вопрос про возврат" in ctx


def test_context_pulls_relevant_knowledge():
    ctx = _proj().build_context("сколько дней на возврат?", k=1)
    assert "Возврат" in ctx
    assert "Гарантия" not in ctx          # нерелевантное не попало


def test_retrieve_respects_k():
    assert len(_proj().retrieve("товар гарантия доставка", k=2)) == 2


def test_add_knowledge_grows_kb():
    p = _proj()
    p.add_knowledge("Промокоды действуют до конца месяца.")
    ctx = p.build_context("есть ли промокоды?", k=1)
    assert "Промокоды" in ctx
