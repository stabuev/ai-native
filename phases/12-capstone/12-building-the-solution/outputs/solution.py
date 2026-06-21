"""Сборка решения: end-to-end процесс из кирпичей курса — Build It для урока 12.2.

Без зависимостей. Capstone собирает изученное в один процесс: маршрутизация по
сложности (Фаза 9) → guardrail (Фаза 7) → вызов инструмента (Фаза 6) → запись в
память (Фазы 4/7) → телеметрия токенов/стоимости (Фаза 10). В проде инструмент —
через MCP, модель — реальная; здесь детерминированные стабы.
"""


def classify(task):
    """Роутинг по сложности (Фаза 9)."""
    return "high" if any(w in task.lower() for w in ("анализ", "код", "сложн", "стратег")) else "low"


# (модель, цена входа, цена выхода за 1M) — как в Фазе 9
ROUTE = {"low": ("haiku-4.5", 1.0, 5.0), "high": ("opus-4.8", 5.0, 25.0)}


class Capstone:
    """End-to-end процесс: роутинг → guardrail → инструмент → память → телеметрия."""

    def __init__(self):
        self.memory = {}
        self.telemetry = []

    def _tool(self, task):
        """Инструмент (в проде — через MCP, Фаза 6)."""
        return f"результат: {task}"

    def run(self, task):
        if not task.strip():                                  # guardrail (Фаза 7)
            raise ValueError("пустая задача")
        level = classify(task)                                # роутинг (Фаза 9)
        model, p_in, p_out = ROUTE[level]
        result = self._tool(task)                             # действие (Фаза 6)
        n_in, n_out = len(task.split()) * 3, 20
        cost = round((n_in * p_in + n_out * p_out) / 1e6, 6)  # стоимость (Фаза 9)
        self.memory[task] = result                            # память (Фазы 4/7)
        self.telemetry.append({"task": task, "model": model,  # телеметрия (Фаза 10)
                               "level": level, "cost": cost})
        return {"result": result, "model": model, "level": level, "cost": cost}

    def total_cost(self):
        return round(sum(t["cost"] for t in self.telemetry), 6)


if __name__ == "__main__":
    cap = Capstone()
    print(cap.run("сделай саммари письма"))           # простое → haiku
    print(cap.run("проведи анализ архитектуры кода"))  # сложное → opus
    print("в памяти задач:", len(cap.memory), "| итого $:", cap.total_cost())
