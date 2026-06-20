"""Анатомия промпта: структурный шаблон + линтер — Build It для урока 2.1.

Без зависимостей. Промпт — это интерфейс к модели, и у него есть анатомия:
роль, контекст, задача, формат ответа, примеры. Здесь собираем промпт из этих
блоков и проверяем линтером, что ключевые части на месте (воспроизводимость).
"""

# Заголовки секций промпта (порядок = рекомендуемая структура).
HEADERS = {
    "role": "# Роль",
    "context": "# Контекст",
    "task": "# Задача",
    "output_format": "# Формат ответа",
    "examples": "# Примеры",
}


def build_prompt(task, role=None, context=None, output_format=None, examples=None):
    """Собрать промпт из блоков. Обязателен только `task`, остальное опционально.

    `examples` — список пар (вход, выход).
    """
    parts = []
    if role:
        parts.append(f"{HEADERS['role']}\n{role}")
    if context:
        parts.append(f"{HEADERS['context']}\n{context}")
    parts.append(f"{HEADERS['task']}\n{task}")
    if output_format:
        parts.append(f"{HEADERS['output_format']}\n{output_format}")
    if examples:
        ex = "\n\n".join(f"Вход: {i}\nВыход: {o}" for i, o in examples)
        parts.append(f"{HEADERS['examples']}\n{ex}")
    return "\n\n".join(parts)


def lint_prompt(text):
    """Каких анатомических блоков не хватает в промпте (эвристика по заголовкам)."""
    return [name for name, header in HEADERS.items() if header not in text]


if __name__ == "__main__":
    bare = build_prompt("Суммаризируй текст в 3 пунктах")
    print("--- голый промпт ---", bare, sep="\n")
    print("\nНе хватает:", lint_prompt(bare))

    full = build_prompt(
        task="Суммаризируй отзыв в 3 пунктах",
        role="Ты редактор продуктовой команды",
        context="Отзывы клиентов из поддержки",
        output_format="Маркированный список из 3 пунктов",
        examples=[("Долго грузит", "- проблема: производительность")],
    )
    print("\n--- полный промпт ---", full, sep="\n")
    print("\nНе хватает:", lint_prompt(full) or "ничего")
