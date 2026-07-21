"""Цикл агента reason -> act -> observe с нуля — Build It для урока 7.1.

Без внешних зависимостей. Показывает суть любого агента: модель (policy)
на каждом шаге выбирает действие — вызвать инструмент или дать финальный
ответ; результат инструмента возвращается в историю, и шаг повторяется.

Здесь policy детерминированная (RuleBasedPolicy), чтобы урок запускался
офлайн и тесты были воспроизводимы. В USE IT та же policy заменяется на
вызов LLM через function calling — форма Action не меняется.
"""
from dataclasses import dataclass, field
from typing import Callable


# ---- Действие, которое выбирает policy на каждом шаге ----
@dataclass
class Action:
    kind: str                 # "tool" | "final"
    tool: str | None = None   # имя инструмента, если kind == "tool"
    args: tuple = ()          # аргументы инструмента
    answer: object = None     # ответ, если kind == "final"


# ---- Запись одного витка цикла (для истории и трейса) ----
@dataclass
class Step:
    action: Action
    observation: object = None


class AgentError(Exception):
    pass


def run_agent(goal: dict, tools: dict[str, Callable], policy: Callable,
              max_steps: int = 10, trace: bool = False) -> tuple[object, list[Step]]:
    """Главный цикл: reason (policy) -> act (tool) -> observe (result).

    Возвращает (финальный_ответ, история_шагов). Если за max_steps агент не
    пришёл к финалу — поднимает AgentError (guardrail против петель).
    """
    history: list[Step] = []
    for _ in range(max_steps):
        action = policy(goal, history)              # reason
        if action.kind == "final":                  # агент решил завершить
            if trace:
                print(f"FINAL -> {action.answer}")
            return action.answer, history
        if action.tool not in tools:                # guardrail: неизвестный инструмент
            raise AgentError(f"unknown tool: {action.tool}")
        observation = tools[action.tool](*action.args)   # act
        history.append(Step(action, observation))        # observe
        if trace:
            print(f"{action.tool}{action.args} -> {observation}")
    raise AgentError(f"no final answer in {max_steps} steps (возможная петля)")


# ---- Инструменты (то, что агент умеет делать руками) ----
def add(x, y): return x + y
def sub(x, y): return x - y
def mul(x, y): return x * y

TOOLS = {"add": add, "sub": sub, "mul": mul}


# ---- Детерминированная policy: цепочка операций над текущим значением ----
class RuleBasedPolicy:
    """Решает goal вида {"start": 2, "ops": [("add", 3), ("mul", 4)]}.

    На каждом шаге берёт текущее значение (start или результат прошлого
    шага), применяет следующую операцию через инструмент, а когда операции
    кончились — отдаёт финальный ответ. Это и есть reason->act->observe.
    """
    def __call__(self, goal: dict, history: list[Step]) -> Action:
        ops = goal["ops"]
        i = len(history)
        value = goal["start"] if i == 0 else history[-1].observation
        if i >= len(ops):
            return Action(kind="final", answer=value)
        name, operand = ops[i]
        return Action(kind="tool", tool=name, args=(value, operand))


if __name__ == "__main__":
    goal = {"start": 2, "ops": [("add", 3), ("mul", 4), ("sub", 1)]}
    answer, history = run_agent(goal, TOOLS, RuleBasedPolicy(), trace=True)
    print(f"\nИтог: (2 + 3) * 4 - 1 = {answer}  за {len(history)} вызова(ов)")
