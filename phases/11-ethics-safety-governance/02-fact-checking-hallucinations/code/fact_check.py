"""Фактчекинг: проверка утверждений на заземление — Build It для урока 11.2.

Без зависимостей. Разбиваем ответ на утверждения и проверяем каждое на
заземлённость в источниках (grounding): есть ли утверждение в нашей базе фактов.
Незаземлённое — кандидат в галлюцинации. В USE IT — перекрёстная проверка
моделями и реальными источниками.
"""
import re


def _tokens(text):
    return set(re.findall(r"\w+", text.lower()))


def extract_claims(text):
    """Разбить текст на утверждения (по предложениям)."""
    return [s.strip() for s in re.split(r"[.!?]\s*", text) if s.strip()]


def verify_claim(claim, sources, threshold=0.4):
    """Заземлено ли утверждение в источниках. 'supported' | 'unsupported'."""
    c = _tokens(claim)
    if not c:
        return "unsupported"
    best = 0.0
    for src in sources:
        s = _tokens(src)
        jaccard = len(c & s) / len(c | s) if (c | s) else 0.0
        best = max(best, jaccard)
    return "supported" if best >= threshold else "unsupported"


def fact_check(text, sources):
    """Отчёт по утверждениям: что заземлено, что нет."""
    return [{"claim": cl, "status": verify_claim(cl, sources)}
            for cl in extract_claims(text)]


if __name__ == "__main__":
    sources = [
        "Возврат товара возможен в течение 14 дней с момента покупки.",
        "Гарантия на электронику составляет 12 месяцев.",
    ]
    answer = "Возврат возможен в течение 14 дней. Гарантия длится 100 лет."
    for r in fact_check(answer, sources):
        print(f"[{r['status']}] {r['claim']}")
