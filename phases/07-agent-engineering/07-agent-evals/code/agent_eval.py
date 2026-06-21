"""Evals агентов: offline-harness на тест-сете — Build It 7.5.

Без зависимостей. Агент нельзя «улучшать на глаз»: нужен фиксированный тест-сет и
метрики (успех задачи, число шагов), чтобы ловить регрессии между версиями. Это
eval-harness из 2.5, но для агента (по итогу/траектории). В USE IT — online-evals в проде.
"""


def task_success(result, expected):
    """Базовая метрика: совпал ли итог с ожидаемым."""
    return 1.0 if result == expected else 0.0


def evaluate_agent(agent_fn, cases, scorer=task_success):
    """Прогнать agent_fn по кейсам {input, expected}. → {success_rate, per_case}."""
    per_case = []
    for c in cases:
        out = agent_fn(c["input"])
        per_case.append({"input": c["input"], "output": out, "score": scorer(out, c["expected"])})
    rate = sum(p["score"] for p in per_case) / len(cases) if cases else 0.0
    return {"success_rate": round(rate, 3), "per_case": per_case}


def compare_versions(versions, cases, scorer=task_success):
    """versions: {name: agent_fn}. Рейтинг по success_rate (по убыванию)."""
    scored = [(n, evaluate_agent(fn, cases, scorer)["success_rate"]) for n, fn in versions.items()]
    return sorted(scored, key=lambda x: x[1], reverse=True)


def has_regression(baseline, candidate, cases, scorer=task_success):
    """True, если кандидат хуже базлайна на тест-сете (защита от регрессий)."""
    b = evaluate_agent(baseline, cases, scorer)["success_rate"]
    c = evaluate_agent(candidate, cases, scorer)["success_rate"]
    return c < b


if __name__ == "__main__":
    cases = [{"input": "2+2", "expected": "4"}, {"input": "3*3", "expected": "9"},
             {"input": "10-7", "expected": "3"}]
    good = lambda x: str(eval(x))                  # noqa: S307 — учебный stub-агент
    broken = lambda x: "?"
    print("good:", evaluate_agent(good, cases)["success_rate"])
    print("broken:", evaluate_agent(broken, cases)["success_rate"])
    print("регрессия good→broken:", has_regression(good, broken, cases))
