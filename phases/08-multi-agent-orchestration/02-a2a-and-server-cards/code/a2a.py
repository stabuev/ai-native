"""A2A и MCP Server Cards — Build It для урока 8.2.

Без зависимостей. Агенты находят друг друга по «карточкам» (что умеет агент) и
передают задачи в стандартном конверте — суть A2A (agent-to-agent) и discovery
через server/agent cards. Здесь матч по навыкам наивный (ключевые слова);
в проде — семантический и по структурированным capability-картам.
"""
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class AgentCard:
    """Карточка агента: имя + навыки (что умеет) + обработчик."""
    name: str
    skills: list = field(default_factory=list)
    handler: Callable = None


def find_agent(task, cards):
    """Выбрать агента, чьи навыки лучше всего покрывают слова задачи (discovery)."""
    words = set(task.lower().split())
    best, best_score = None, 0
    for card in cards:
        score = sum(1 for skill in card.skills if skill in words)
        if score > best_score:
            best, best_score = card, score
    return best


def send_task(task, card):
    """A2A: передать задачу агенту, вернуть конверт результата."""
    if card is None:
        return {"status": "no_agent", "task": task, "result": None}
    return {"status": "done", "agent": card.name, "task": task,
            "result": card.handler(task)}


def route_and_run(task, cards):
    """Найти подходящего агента по карточкам и выполнить задачу."""
    return send_task(task, find_agent(task, cards))


if __name__ == "__main__":
    cards = [
        AgentCard("sql-agent", ["sql", "база", "запрос"], lambda t: "SELECT ..."),
        AgentCard("doc-agent", ["документ", "поиск", "rag"], lambda t: "найдено 3 документа"),
    ]
    print(route_and_run("сделай sql запрос", cards))
    print(route_and_run("поиск по документам", cards))
    print(route_and_run("нарисуй картинку", cards))      # нет агента
