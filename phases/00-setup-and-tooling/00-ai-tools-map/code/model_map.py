"""Карта моделей ИИ 2026 + рекомендатор «задача → модель» — Build It для урока 0.1.

Без внешних зависимостей. Хранит реестр моделей (провайдер, цена входа/выхода,
тир, сильные стороны) и подбирает модель под профиль задачи. Идея урока: не
«одна модель на всё», а осознанный выбор по сложности, объёму, цене и задержке.

Цены — ориентировочные, $ за 1M токенов (см. README, «Карта моделей и цен 2026»).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Model:
    name: str
    provider: str
    price_in: float      # $ за 1M входных токенов
    price_out: float     # $ за 1M выходных токенов (для Flash ≈, выход дешёвый)
    tier: int            # 1 — дешёвый/быстрый ... 4 — топ
    good_for: tuple      # короткие подсказки «когда брать»


# Реестр отсортирован по тиру (от дешёвого к топовому).
REGISTRY = (
    Model("Gemini Flash",     "Google",    0.30,  2.50, 1, ("массовые задачи", "классификация")),
    Model("Claude Haiku 4.5", "Anthropic", 1.00,  5.00, 2, ("рутина", "черновики", "извлечение")),
    Model("GPT-5.x",          "OpenAI",    2.50, 15.00, 3, ("универсальные задачи",)),
    Model("Claude Sonnet 4.6","Anthropic", 3.00, 15.00, 3, ("рабочая лошадка",)),
    Model("Claude Opus 4.8",  "Anthropic", 5.00, 25.00, 4, ("сложное рассуждение", "код", "анализ")),
)


@dataclass
class Task:
    """Профиль задачи, по которому подбираем модель."""
    complexity: str = "medium"   # "low" | "medium" | "high"
    high_volume: bool = False    # массовая обработка (тысячи вызовов)
    needs_code: bool = False     # генерация/разбор кода
    budget_sensitive: bool = False


def by_name(name):
    for m in REGISTRY:
        if m.name == name:
            return m
    raise KeyError(name)


def estimate_cost(model, n_in, n_out):
    """Стоимость одного вызова в $ по числу токенов входа/выхода."""
    return n_in / 1e6 * model.price_in + n_out / 1e6 * model.price_out


def recommend(task):
    """Подобрать модель под профиль задачи. Возвращает (Model, обоснование)."""
    if task.complexity == "high" or task.needs_code:
        return by_name("Claude Opus 4.8"), "высокая сложность/код → топ-модель"
    if task.high_volume or task.budget_sensitive:
        if task.complexity == "low":
            return by_name("Gemini Flash"), "массовость + простота → самый дешёвый тир"
        return by_name("Claude Haiku 4.5"), "массовость/экономия → дешёвый тир"
    return by_name("Claude Sonnet 4.6"), "обычная задача → рабочая лошадка"


if __name__ == "__main__":
    samples = [
        Task(complexity="low", high_volume=True),
        Task(complexity="medium"),
        Task(complexity="high", needs_code=True),
    ]
    for t in samples:
        m, why = recommend(t)
        cost = estimate_cost(m, 1000, 500)
        print(f"{t}\n  → {m.name} ({m.provider}) | {why} | ~${cost:.4f} за вызов 1k/500\n")
