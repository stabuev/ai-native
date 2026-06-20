"""Движок квиза /check-understanding — Build It (companion) урока 0.3.

Офлайн, без зависимостей. По банку вопросов фазы считает результат, выдаёт
вердикт и список уроков на повтор по неверным ответам. Используется после
ключевых фаз (1, 4, 8). Здесь приведён банк для Фазы 1 как образец; банки
других фаз добавляются по мере готовности уроков.
"""
from __future__ import annotations

# Для каждой фазы — список вопросов {q, options, correct (индекс), lesson}.
BANKS = {
    1: [
        {"q": "Что модель видит на входе?",
         "options": ["слова", "символы", "токены", "байты"], "correct": 2, "lesson": "1.1"},
        {"q": "За что выставляется счёт API?",
         "options": ["за запросы", "за токены (вход+выход)", "за время", "за символы"],
         "correct": 1, "lesson": "1.1"},
        {"q": "Температура 0 даёт…",
         "options": ["случайность", "самый вероятный токен", "ошибку", "длинный ответ"],
         "correct": 1, "lesson": "1.3"},
        {"q": "top-p (nucleus) отсекает кандидатов…",
         "options": ["по числу токенов", "по сумме вероятностей", "по длине", "по алфавиту"],
         "correct": 1, "lesson": "1.3"},
        {"q": "Галлюцинация — это…",
         "options": ["сбой сети", "уверенно неверный ответ", "превышение лимита", "таймаут"],
         "correct": 1, "lesson": "1.4"},
    ],
}

PASS_THRESHOLD = 0.8


def grade(answers, bank) -> dict:
    """answers: список выбранных индексов. Возвращает результат и список повтора."""
    assert len(answers) == len(bank), "нужен ответ на каждый вопрос"
    correct = sum(a == q["correct"] for a, q in zip(answers, bank))
    review = sorted({q["lesson"] for a, q in zip(answers, bank) if a != q["correct"]})
    s = correct / len(bank)
    return {
        "correct": correct, "total": len(bank), "score": round(s, 2),
        "verdict": "сдано" if s >= PASS_THRESHOLD else "повторить",
        "review_lessons": review,
    }


def run_quiz(phase: int, answers) -> dict:
    if phase not in BANKS:
        raise KeyError(f"нет банка вопросов для фазы {phase}")
    return grade(answers, BANKS[phase])


if __name__ == "__main__":
    bank = BANKS[1]
    perfect = [q["correct"] for q in bank]
    print("Все верно:", run_quiz(1, perfect))
    mixed = perfect.copy(); mixed[0] = (mixed[0] + 1) % 4
    print("Одна ошибка:", run_quiz(1, mixed))
