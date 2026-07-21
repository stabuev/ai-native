"""Корпоративные политики ИИ: шаблон + проверки — Build It для урока 11.4.

Без зависимостей. Политика использования ИИ должна покрывать ключевые разделы, а
конкретный кейс — проверяться против правил (PII во внешнюю модель, автоматические
решения о людях и т.п.). Здесь валидируем полноту политики и решаем по кейсу.
"""

REQUIRED_SECTIONS = (
    "Допустимые данные",
    "Запрещённые данные",
    "Одобренные инструменты",
    "Проверка человеком",
    "Ответственность",
)


def validate_policy(text):
    """Вернуть список отсутствующих обязательных разделов (пустой = политика полная)."""
    return [s for s in REQUIRED_SECTIONS if s not in text]


def check_usecase(sends_pii=False, external=False, automated_decision=False):
    """Решение по кейсу против базовых правил. → {allowed, reason}."""
    if sends_pii and external:
        return {"allowed": False, "reason": "PII нельзя отдавать во внешнюю модель"}
    if automated_decision:
        return {"allowed": False, "reason": "решения о людях требуют проверки человеком"}
    return {"allowed": True, "reason": "разрешено политикой"}


if __name__ == "__main__":
    policy = ("# Политика ИИ\n## Допустимые данные\n...\n## Запрещённые данные\n...\n"
              "## Одобренные инструменты\n...\n## Проверка человеком\n...")
    print("Не хватает разделов:", validate_policy(policy) or "нет")
    print("PII во внешнюю:", check_usecase(sends_pii=True, external=True))
    print("Автоскоринг людей:", check_usecase(automated_decision=True))
    print("Саммари публичных данных:", check_usecase())
