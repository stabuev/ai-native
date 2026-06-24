"""Карта моделей ИИ 2026 + калькулятор стоимости запроса — Build It для урока 0.1.

Без внешних зависимостей. Хранит реестр моделей (провайдер, цена входа/выхода,
тир, сильные стороны) и считает, во что обойдётся вызов, ДО отправки в API.
Идея урока: цена запроса предсказуема — её можно прикинуть заранее и не платить
за топ-модель там, где справится дешёвая. (Автоматический выбор модели — тема Фазы 9.)

Цены — ориентировочные, $ за 1M токенов (см. README, «Карта моделей и цен 2026»).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Model:
    name: str
    provider: str
    price_in: float      # $ за 1M входных токенов
    price_out: float     # $ за 1M выходных токенов
    tier: int            # 1 — дешёвый/быстрый ... 4 — топ
    good_for: tuple      # короткие подсказки «когда брать»


# Реестр отсортирован по тиру (от дешёвого к топовому).
REGISTRY = (
    Model("DeepSeek V4-Flash","DeepSeek",  0.14,  0.28, 1, ("дёшево", "reasoning", "open-weight/self-host")),
    Model("Gemini Flash",     "Google",    0.30,  2.50, 1, ("массовые задачи", "классификация")),
    Model("Claude Haiku 4.5", "Anthropic", 1.00,  5.00, 2, ("рутина", "черновики", "извлечение")),
    Model("GPT-5.x",          "OpenAI",    2.50, 15.00, 3, ("универсальные задачи",)),
    Model("Claude Sonnet 4.6","Anthropic", 3.00, 15.00, 3, ("рабочая лошадка",)),
    Model("Claude Opus 4.8",  "Anthropic", 5.00, 25.00, 4, ("сложное рассуждение", "код", "анализ")),
)


def by_name(name):
    """Найти модель в реестре по имени."""
    for m in REGISTRY:
        if m.name == name:
            return m
    raise KeyError(name)


def estimate_cost(model, n_in, n_out):
    """Стоимость одного вызова в $ по числу токенов входа/выхода."""
    return n_in / 1e6 * model.price_in + n_out / 1e6 * model.price_out


if __name__ == "__main__":
    # «Будет ли дорого?» — прикидка ДО отправки запроса.
    # Пример из урока: классификация одного тикета ~200 токенов вход / ~20 выход.
    n_in, n_out, batch = 200, 20, 10_000
    print(f"Один тикет: {n_in} ток. вход / {n_out} ток. выход · партия {batch:,}\n")
    for m in REGISTRY:
        per_call = estimate_cost(m, n_in, n_out)
        print(f"  {m.name:18} ${per_call:.5f}/вызов   ${per_call * batch:7.2f} на {batch:,}")
