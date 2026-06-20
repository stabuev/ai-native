"""Mini eval-harness: метрики и сравнение версий промптов — Build It для урока 2.5.

Без зависимостей. Прогоняет промпт-функцию по набору кейсов {input, expected},
считает метрику и сравнивает версии промптов между собой. Промпт-функция здесь —
обычный callable (в тестах детерминированный stub); в USE IT её роль играет
вызов модели. Это ядро фазы: «писать воспроизводимые промпты и измерять качество».
"""


# --- метрики: (pred, expected) -> [0..1] ---
def exact_match(pred, expected):
    return 1.0 if pred.strip() == expected.strip() else 0.0


def contains(pred, expected):
    return 1.0 if expected.lower() in pred.lower() else 0.0


def evaluate(prompt_fn, cases, metric=exact_match):
    """Прогнать prompt_fn по кейсам. Возвращает {score, per_case}."""
    per_case = []
    for c in cases:
        pred = prompt_fn(c["input"])
        per_case.append({"input": c["input"], "pred": pred,
                         "expected": c["expected"], "score": metric(pred, c["expected"])})
    score = sum(p["score"] for p in per_case) / len(cases) if cases else 0.0
    return {"score": score, "per_case": per_case}


def compare(versions, cases, metric=exact_match):
    """versions: {name: prompt_fn}. Рейтинг (name, score) по убыванию качества."""
    scored = [(name, evaluate(fn, cases, metric)["score"]) for name, fn in versions.items()]
    return sorted(scored, key=lambda x: x[1], reverse=True)


if __name__ == "__main__":
    cases = [
        {"input": "2+2", "expected": "4"},
        {"input": "3+5", "expected": "8"},
        {"input": "10-4", "expected": "6"},
    ]
    # две «версии промпта»: рабочая и сломанная
    good = lambda x: str(eval(x))               # noqa: S307 — учебный stub
    bad = lambda x: "не знаю"
    print("good:", evaluate(good, cases)["score"])
    print("bad :", evaluate(bad, cases)["score"])
    print("рейтинг:", compare({"good": good, "bad": bad}, cases))
