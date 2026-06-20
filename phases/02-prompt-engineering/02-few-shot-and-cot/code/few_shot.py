"""Few-shot и chain-of-thought — Build It для урока 2.2.

Без зависимостей. Показывает, ЗАЧЕМ примеры в промпте: на игрушечной задаче
few-shot (решение по примерам) бьёт zero-shot (без примеров). Плюс сборщики
few-shot и CoT промптов, которые дальше переносятся на реальную модель.
"""


def format_few_shot(instruction, examples, query):
    """Few-shot промпт: инструкция + примеры (вход→выход) + запрос."""
    lines = [instruction, ""]
    for inp, out in examples:
        lines.append(f"Вход: {inp}\nВыход: {out}\n")
    lines.append(f"Вход: {query}\nВыход:")
    return "\n".join(lines)


def format_cot(instruction, query):
    """CoT-вариант: попросить рассуждать пошагово перед финальным ответом."""
    return f"{instruction}\n\nЗадача: {query}\nДумай по шагам, затем дай ответ."


# --- демонстрация ценности примеров на игрушечной задаче классификации ---
def _similarity(a, b):
    """Похожесть по доле общих слов (Жаккар)."""
    sa, sb = set(a.split()), set(b.split())
    return len(sa & sb) / len(sa | sb) if (sa | sb) else 0.0


def knn_predict(query, examples):
    """Few-shot аналог: метка самого похожего примера."""
    if not examples:
        return None
    return max(examples, key=lambda e: _similarity(query, e[0]))[1]


def zero_shot_predict(query, default):
    """Без примеров модель «угадывает» — берём дефолтную метку."""
    return default


def accuracy(predict_fn, dataset):
    """Доля верных предсказаний на наборе (вход, метка)."""
    return sum(predict_fn(x) == y for x, y in dataset) / len(dataset)


if __name__ == "__main__":
    examples = [
        ("обожаю прекрасный фильм", "pos"),
        ("чудесный замечательный день", "pos"),
        ("ненавижу отвратительную еду", "neg"),
        ("ужасный кошмарный сервис", "neg"),
    ]
    test = [("обожаю прекрасный сериал", "pos"), ("ужасный кошмарный продукт", "neg")]
    print("few-shot промпт:\n", format_few_shot("Классифицируй тональность.", examples, "ужасный кошмарный фильм"))
    print("\nfew-shot accuracy:", accuracy(lambda x: knn_predict(x, examples), test))
    print("zero-shot accuracy:", accuracy(lambda x: zero_shot_predict(x, "neg"), test))
