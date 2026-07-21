"""Паттерны экономии: роутер + каскад с quality-gate — Build It для урока 9.3.

Без зависимостей. Каскад: сначала пробуем дешёвую модель; если качество ответа ниже
порога (quality-gate) — эскалируем на более сильную. Так платим за топ-модель только
там, где она реально нужна. Цены — как в 9.1, проверка качества — стаб (в проде LLM-judge).
"""

# Каскад от дешёвого к дорогому + цена за «вызов» (усл. единицы, см. 9.1).
CASCADE = [("gemini-flash", 1), ("sonnet-4.6", 10), ("opus-4.8", 30)]


def cascade(request, answer_fn, quality_fn, gate=0.7, ladder=CASCADE):
    """Идти по лестнице моделей, пока качество >= gate. Возвращает результат + стоимость.

    answer_fn(model, request) -> ответ; quality_fn(request, answer) -> [0..1].
    """
    spent = 0
    last = None
    for model, price in ladder:
        spent += price
        answer = answer_fn(model, request)
        q = quality_fn(request, answer)
        last = {"model": model, "answer": answer, "quality": q, "cost": spent}
        if q >= gate:
            return last
    return last          # дошли до топа — отдаём лучший доступный


def always_top_cost(ladder=CASCADE):
    return ladder[-1][1]


if __name__ == "__main__":
    # стаб: дешёвая модель хороша на простом, плоха на сложном
    def answer_fn(model, req):
        return f"[{model}] ответ"

    def quality_fn(req, ans):
        hard = "сложн" in req.lower()
        if hard:
            return 0.9 if "opus" in ans else 0.4      # только opus тянет сложное
        return 0.9                                     # простое тянет любая

    print("простой:", cascade("простой вопрос", answer_fn, quality_fn))
    print("сложный:", cascade("сложный вопрос", answer_fn, quality_fn))
