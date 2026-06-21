"""Конфиденциальность: классификация данных + PII — Build It для урока 11.1.

Без зависимостей. Прежде чем отдать текст модели, надо понять, что в нём: PII,
секреты, корпоративная тайна. Классифицируем чувствительность, находим и
маскируем PII и решаем, можно ли отправлять во внешнюю модель.
"""
import re

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?:\+7|8)[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}")
CARD = re.compile(r"\b(?:\d[ -]?){13,16}\b")
SECRET = re.compile(r"(?:sk-[A-Za-z0-9_-]{8,}|AKIA[0-9A-Z]{12,})")

PATTERNS = {"email": EMAIL, "phone": PHONE, "card": CARD, "secret": SECRET}
ORDER = ["public", "internal", "confidential", "restricted"]


def detect_pii(text):
    """Вернуть найденные PII/секреты: список {type, value}."""
    found = []
    for kind, pat in PATTERNS.items():
        for m in pat.finditer(text):
            found.append({"type": kind, "value": m.group()})
    return found


def classify_sensitivity(text):
    """Уровень чувствительности по найденным сущностям/маркерам."""
    kinds = {f["type"] for f in detect_pii(text)}
    if {"secret", "card"} & kinds:
        return "restricted"
    if {"email", "phone"} & kinds:
        return "confidential"
    if re.search(r"внутрен|конфиденциаль|для служебного", text, re.IGNORECASE):
        return "internal"
    return "public"


def redact(text):
    """Замаскировать PII/секреты плейсхолдерами."""
    for kind, pat in PATTERNS.items():
        text = pat.sub(f"[{kind.upper()}]", text)
    return text


def can_send(level, max_allowed="internal"):
    """Можно ли отдавать данные уровня level во внешнюю модель (порог max_allowed)."""
    return ORDER.index(level) <= ORDER.index(max_allowed)


if __name__ == "__main__":
    text = "Клиент Иван, почта ivan@mail.ru, тел +7 999 123 45 67, ключ sk-secret123token"
    print("PII:", detect_pii(text))
    print("Уровень:", classify_sensitivity(text))
    print("Маска:", redact(text))
    print("Можно во внешнюю модель?", can_send(classify_sensitivity(text)))
