"""Декомпозиция: цепочка промптов — Build It для урока 2.3.

Без зависимостей. Сложную задачу разбиваем на шаги; выход каждого шага — вход
следующего. Здесь шаги — детерминированные функции (вместо вызова LLM), чтобы
урок шёл офлайн; в USE IT каждый шаг становится отдельным промптом к модели.
"""
from dataclasses import dataclass
from typing import Callable


@dataclass
class ChainStep:
    name: str
    fn: Callable          # callable(value) -> value


def run_chain(steps, initial, trace=False):
    """Прогнать значение через цепочку шагов. Возвращает (итог, история)."""
    value = initial
    history = []
    for step in steps:
        out = step.fn(value)
        history.append({"step": step.name, "in": value, "out": out})
        if trace:
            print(f"{step.name}: {value!r} -> {out!r}")
        value = out
    return value, history


# --- демонстрация декомпозиции: «посчитай сумму чисел из текста и оформи» ---
def _extract_numbers(text):
    return [int(w) for w in text.split() if w.lstrip("-").isdigit()]


def _sum(nums):
    return sum(nums)


def _format(total):
    return f"Итого: {total}"


DEMO_CHAIN = [
    ChainStep("extract", _extract_numbers),
    ChainStep("sum", _sum),
    ChainStep("format", _format),
]


if __name__ == "__main__":
    answer, history = run_chain(DEMO_CHAIN, "купил 2 яблока, 3 груши и 5 слив", trace=True)
    print("\nИтог:", answer, f"({len(history)} шага)")
