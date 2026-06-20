"""Контекст-инжиниринг: сборка и компакция контекста — Build It для урока 4.4.

Без зависимостей. Контекстное окно конечно (урок 1.2): собираем слои (system,
память, RAG, история) по приоритету и при нехватке бюджета отбрасываем наименее
важное (компакция). Это политика «что и в каком порядке кладём в окно».
"""


def estimate_tokens(text):
    """Грубая оценка токенов ≈ число слов (учебно; реально — токенайзером, урок 1.1)."""
    return len(text.split())


def assemble(layers, budget):
    """Собрать контекст под бюджет токенов.

    layers: [{name, content, priority}] — priority больше = важнее.
    Возвращает {kept, dropped, tokens}: берём по убыванию приоритета, пока влезает.
    """
    ordered = sorted(layers, key=lambda layer: layer["priority"], reverse=True)
    kept, dropped, used = [], [], 0
    for layer in ordered:
        cost = estimate_tokens(layer["content"])
        if used + cost <= budget:
            kept.append(layer)
            used += cost
        else:
            dropped.append(layer)
    return {"kept": kept, "dropped": dropped, "tokens": used}


def compact_history(history, max_items):
    """Оставить последние max_items сообщений (старое «забываем»)."""
    if max_items < 0:
        return list(history)
    return history[-max_items:]


def _words(n, tag="w"):
    return " ".join([tag] * n)


if __name__ == "__main__":
    layers = [
        {"name": "system", "content": _words(20), "priority": 4},
        {"name": "rag", "content": _words(30), "priority": 3},
        {"name": "memory", "content": _words(20), "priority": 2},
        {"name": "history", "content": _words(40), "priority": 1},
    ]
    res = assemble(layers, budget=60)
    print("Влезло:", [l["name"] for l in res["kept"]], "| токенов:", res["tokens"])
    print("Отброшено:", [l["name"] for l in res["dropped"]])
    print("История (last 2):", compact_history(["m1", "m2", "m3", "m4"], 2))
