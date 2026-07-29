"""Проверяемый план контекста — Build It для урока 4.4.

Без зависимостей и вызовов модели. Код не изображает «идеальный» context
engineering: человек или приложение заранее решает, что обязательно и насколько
каждый необязательный элемент релевантен текущей задаче. Планировщик делает это
решение наблюдаемым: считает учебные единицы, соблюдает бюджет и объясняет потери.
"""


def estimate_units(text):
    """Вернуть число слов как учебную единицу бюджета, но не как число токенов."""
    return len(text.split())


def compact_history(history, summary, keep_recent=2):
    """Соединить резюме старой истории с несколькими последними сообщениями.

    Функция не создаёт резюме: его готовит человек или модель. Если старые
    сообщения будут исключены, пустое резюме запрещено — так важное не исчезает
    молча.
    """
    if keep_recent < 0:
        raise ValueError("keep_recent must be non-negative")

    recent = list(history[-keep_recent:]) if keep_recent else []
    omitted = len(history) - len(recent)
    clean_summary = summary.strip()
    if omitted and not clean_summary:
        raise ValueError("summary is required when older history is omitted")

    return {
        "summary": clean_summary,
        "recent": recent,
        "omitted": omitted,
    }


def plan_context(items, budget, reserve=0):
    """Собрать проверяемый план контекста для одного вызова модели.

    items: список словарей с полями id, source, content, required, relevance.
    required=True означает «нельзя молча исключить». relevance оценивается для
    текущей задачи: 0 — не относится к ней, большее значение — полезнее.

    budget — общий учебный бюджет, reserve — часть под будущий ответ.
    Возвращается manifest с kept/dropped и причиной каждого исключения.
    """
    if budget < 0 or reserve < 0 or reserve > budget:
        raise ValueError("budget and reserve must satisfy 0 <= reserve <= budget")

    input_budget = budget - reserve
    required = [item for item in items if item.get("required", False)]
    optional = [item for item in items if not item.get("required", False)]
    optional = sorted(optional, key=lambda item: item.get("relevance", 0), reverse=True)

    required_cost = sum(estimate_units(item["content"]) for item in required)
    if required_cost > input_budget:
        raise ValueError("required context exceeds the input budget")

    kept = [_manifest_entry(item) for item in required]
    dropped = []
    used = required_cost

    for item in optional:
        entry = _manifest_entry(item)
        if item.get("relevance", 0) <= 0:
            entry["reason"] = "not_relevant"
            dropped.append(entry)
        elif used + entry["units"] <= input_budget:
            kept.append(entry)
            used += entry["units"]
        else:
            entry["reason"] = "budget"
            dropped.append(entry)

    return {
        "kept": kept,
        "dropped": dropped,
        "used_units": used,
        "input_budget_units": input_budget,
        "reserve_units": reserve,
    }


def _manifest_entry(item):
    """Оставить в manifest только поля, нужные для проверки решения."""
    entry = {
        "id": item["id"],
        "source": item["source"],
        "content": item["content"],
        "required": item.get("required", False),
        "relevance": item.get("relevance", 0),
        "units": estimate_units(item["content"]),
    }
    if "source_ref" in item:
        entry["source_ref"] = dict(item["source_ref"])
    return entry


if __name__ == "__main__":
    history = compact_history(
        ["Обсудили формат.", "Выбрали таблицу.", "Проверили черновик."],
        summary="Решение: показать итог таблицей.",
        keep_recent=1,
    )
    history_text = " ".join([history["summary"], *history["recent"]])

    candidates = [
        {
            "id": "instructions",
            "source": "project",
            "content": "Отвечай только по действующей политике.",
            "required": True,
            "relevance": 3,
        },
        {
            "id": "request",
            "source": "user",
            "content": "Какой сейчас срок возврата товара?",
            "required": True,
            "relevance": 3,
        },
        {
            "id": "policy-v2",
            "source": "rag",
            "content": "Действующая политика: возврат возможен в течение тридцати дней.",
            "required": False,
            "relevance": 3,
        },
        {
            "id": "format-preference",
            "source": "memory",
            "content": "Пользователь предпочитает краткий ответ.",
            "required": False,
            "relevance": 2,
            "source_ref": {
                "owner": "support-project",
                "key": "response.format",
                "record_id": 0,
            },
        },
        {
            "id": "history-summary",
            "source": "history",
            "content": history_text,
            "required": False,
            "relevance": 1,
        },
        {
            "id": "policy-v1",
            "source": "rag",
            "content": "Архивная политика: возврат возможен в течение четырнадцати дней.",
            "required": False,
            "relevance": 0,
        },
    ]

    result = plan_context(candidates, budget=30, reserve=6)
    print("В контексте:", [item["id"] for item in result["kept"]])
    print("Исключено:", [(item["id"], item["reason"]) for item in result["dropped"]])
    print(
        "Бюджет:",
        result["used_units"],
        "/",
        result["input_budget_units"],
        "+ резерв",
        result["reserve_units"],
    )
