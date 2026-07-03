"""Движок входного квиза /find-your-level — Build It для урока 0.3.

Без зависимостей и офлайн. 10 вопросов с весами (0..3 за вопрос), по сумме
баллов определяет уровень студента и строит персональный маршрут по курсу с
оценкой часов. Тот же движок упакован в скилл (см. outputs/ и .claude/skills/).
"""
from __future__ import annotations

# Каждый вопрос: текст + варианты (label, score 0..3).
QUESTIONS = [
    {"q": "Python",            "options": [("не писал", 0), ("скрипты по примеру", 1), ("свои функции/модули", 2), ("пакеты, тесты, типы", 3)]},
    {"q": "Терминал/Linux",    "options": [("боюсь", 0), ("базовые команды", 1), ("env, pipes, процессы", 2), ("свободно", 3)]},
    {"q": "git",               "options": [("нет", 0), ("commit/push", 1), ("ветки/merge", 2), ("rebase/CI", 3)]},
    {"q": "Вызов LLM API",     "options": [("никогда", 0), ("через UI", 1), ("пару раз кодом", 2), ("в проде", 3)]},
    {"q": "Промптинг",         "options": [("интуитивно", 0), ("знаю few-shot", 1), ("CoT, форматы", 2), ("делаю eval", 3)]},
    {"q": "RAG/эмбеддинги",    "options": [("что это", 0), ("слышал", 1), ("пробовал", 2), ("строил", 3)]},
    {"q": "Агенты/tool use",   "options": [("нет", 0), ("читал", 1), ("запускал", 2), ("писал свои", 3)]},
    {"q": "MCP",               "options": [("впервые слышу", 0), ("знаю идею", 1), ("подключал", 2), ("писал сервер", 3)]},
    {"q": "SQL/аналитика",     "options": [("нет", 0), ("простые SELECT", 1), ("джоины/окна", 2), ("свободно", 3)]},
    {"q": "Стоимость/FinOps",  "options": [("не думал", 0), ("примерно", 1), ("считаю токены", 2), ("оптимизирую роутингом", 3)]},
]

# (id, название, базовые часы) — сумма = 228 (см. README / ROADMAP, дорожная карта).
PHASES = [
    (0, "Setup & Tooling", 8), (1, "Как работают LLM", 12), (2, "Промпт-инжиниринг", 16),
    (3, "Текст и документы", 18), (4, "Скиллы, память, проекты", 20), (5, "Данные и аналитика", 18),
    (6, "Инструменты и MCP", 18), (7, "Agent Engineering", 26), (8, "Мульти-агенты", 18),
    (9, "FinOps", 14), (10, "Production", 16), (11, "Этика и governance", 14), (12, "Capstone", 30),
]

_FACTOR = {"focus": 1.0, "skim": 0.5, "skip": 0.0}


def score(answers) -> int:
    """Сумма баллов по выбранным индексам (0..3 за вопрос). Диапазон 0..30."""
    assert len(answers) == len(QUESTIONS), "нужен ответ на каждый вопрос"
    return sum(QUESTIONS[i]["options"][choice][1] for i, choice in enumerate(answers))


def level(total: int) -> str:
    if total < 10:
        return "Новичок"
    if total <= 20:
        return "Практик"
    return "Инженер"


def _action(lvl: str, pid: int) -> str:
    """Что делать с фазой при данном уровне. Capstone всегда focus."""
    if pid == 12:
        return "focus"
    if lvl == "Новичок":
        return "focus"
    if lvl == "Практик":
        return "skim" if pid in (0, 1) else "focus"   # уже знает setup и базу LLM
    # Инженер
    if pid == 0:
        return "skip"
    return "skim" if pid in (1, 2) else "focus"


def route(total: int) -> dict:
    """Персональный маршрут: действие и часы по каждой фазе + итог по часам."""
    lvl = level(total)
    plan, hours = [], 0.0
    for pid, name, base in PHASES:
        action = _action(lvl, pid)
        h = base * _FACTOR[action]
        hours += h
        plan.append({"phase": pid, "name": name, "action": action, "hours": h})
    return {"level": lvl, "score": total, "total_hours": hours, "plan": plan}


if __name__ == "__main__":
    for answers, who in [([0] * 10, "новичок"), ([2] * 10, "практик"), ([3] * 10, "инженер")]:
        r = route(score(answers))
        print(f"{who}: {r['level']}, балл {r['score']}, ~{r['total_hours']:.0f} ч")
