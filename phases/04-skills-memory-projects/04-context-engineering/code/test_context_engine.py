import pytest

from context_engine import compact_history, estimate_units, plan_context


def item(item_id, source, content, *, required=False, relevance=0):
    return {
        "id": item_id,
        "source": source,
        "content": content,
        "required": required,
        "relevance": relevance,
    }


def test_estimate_units_counts_words_without_calling_them_tokens():
    assert estimate_units("раз два три") == 3


def test_required_instructions_and_current_request_are_never_silently_dropped():
    items = [
        item("instructions", "project", "следуй действующей политике", required=True),
        item("request", "user", "какой срок возврата", required=True),
        item("large-rag", "rag", "слово " * 20, relevance=3),
    ]

    result = plan_context(items, budget=10, reserve=3)

    assert [entry["id"] for entry in result["kept"]] == ["instructions", "request"]
    assert result["dropped"][0]["id"] == "large-rag"
    assert result["dropped"][0]["reason"] == "budget"


def test_relevance_belongs_to_an_item_not_to_its_source_layer():
    items = [
        item("request", "user", "подготовь краткую таблицу", required=True),
        item("useful-memory", "memory", "покажи ответ таблицей", relevance=3),
        item("archived-rag", "rag", "архивная версия правил", relevance=0),
    ]

    result = plan_context(items, budget=8)

    assert [entry["id"] for entry in result["kept"]] == ["request", "useful-memory"]
    assert result["dropped"][0]["id"] == "archived-rag"
    assert result["dropped"][0]["reason"] == "not_relevant"


def test_required_context_overflow_stops_instead_of_hiding_the_failure():
    items = [
        item("instructions", "project", "один два три четыре", required=True),
        item("request", "user", "пять шесть семь", required=True),
    ]

    with pytest.raises(ValueError, match="required context"):
        plan_context(items, budget=8, reserve=2)


def test_manifest_explains_budget_and_reserves_space_for_the_answer():
    items = [
        item("request", "user", "раз два", required=True),
        item("fact-a", "rag", "три четыре пять", relevance=3),
        item("fact-b", "memory", "шесть семь восемь", relevance=2),
    ]

    result = plan_context(items, budget=8, reserve=2)

    assert result["input_budget_units"] == 6
    assert result["reserve_units"] == 2
    assert result["used_units"] == 5
    assert [entry["id"] for entry in result["kept"]] == ["request", "fact-a"]
    assert result["dropped"][0]["reason"] == "budget"


def test_compaction_keeps_a_summary_and_recent_messages():
    result = compact_history(
        ["решили формат", "выбрали источник", "проверили ответ", "спасибо"],
        summary="Решили использовать действующий источник.",
        keep_recent=2,
    )

    assert result == {
        "summary": "Решили использовать действующий источник.",
        "recent": ["проверили ответ", "спасибо"],
        "omitted": 2,
    }


def test_compaction_refuses_silent_truncation():
    with pytest.raises(ValueError, match="summary"):
        compact_history(["важное решение", "новое сообщение"], summary="", keep_recent=1)
