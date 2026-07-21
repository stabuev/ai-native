"""Память и планирование агента — Build It для урока 7.2.

Без зависимостей. Поверх цикла из 7.1 добавляем две вещи: ПЛАН (декомпозиция
цели на шаги, как в 2.3) и ПАМЯТЬ (промежуточные результаты переживают шаги, как
в 4.2). Каждый шаг читает прошлое значение из памяти и пишет новое — так агент
ведёт многошаговую задачу, не теряя состояние.
"""


class Memory:
    """Простейшая рабочая память агента (ключ → значение)."""

    def __init__(self):
        self.store = {}

    def remember(self, key, value):
        self.store[key] = value

    def recall(self, key, default=None):
        return self.store.get(key, default)


TOOLS = {"add": lambda a, b: a + b, "sub": lambda a, b: a - b, "mul": lambda a, b: a * b}


def plan(goal):
    """Декомпозиция цели в упорядоченные шаги. goal = {start, ops:[(op, operand)]}."""
    return [{"op": op, "operand": operand} for op, operand in goal["ops"]]


def run(goal, memory=None):
    """Выполнить план, неся состояние через память. Возвращает (итог, память, трейс)."""
    memory = memory or Memory()
    memory.remember("value", goal["start"])
    trace = []
    for i, step in enumerate(plan(goal)):
        prev = memory.recall("value")                      # читаем из памяти
        result = TOOLS[step["op"]](prev, step["operand"])
        memory.remember("value", result)                   # пишем в память
        memory.remember(f"step_{i}", result)               # история шагов
        trace.append({"step": i, "op": step["op"], "operand": step["operand"], "result": result})
    return memory.recall("value"), memory, trace


if __name__ == "__main__":
    goal = {"start": 2, "ops": [("add", 3), ("mul", 4), ("sub", 1)]}   # (2+3)*4-1
    answer, memory, trace = run(goal)
    for t in trace:
        print(t)
    print("Итог:", answer, "| память:", memory.store)
