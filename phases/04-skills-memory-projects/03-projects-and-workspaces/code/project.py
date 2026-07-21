"""Проекты и рабочие пространства — Build It для урока 4.3.

Без зависимостей. Проект = system prompt + база знаний (+ память). На запрос
собирает контекст: системная инструкция + релевантные куски знаний. Это
объединяет skills/memory/RAG в переиспользуемое рабочее пространство.
"""
import re
from collections import Counter


def _tokens(text):
    return re.findall(r"\w+", text.lower())


class Project:
    """Рабочее пространство: постоянная инструкция + база знаний."""

    def __init__(self, name, system_prompt, knowledge=None):
        self.name = name
        self.system_prompt = system_prompt
        self.knowledge = list(knowledge or [])

    def add_knowledge(self, doc):
        self.knowledge.append(doc)

    def retrieve(self, query, k=3):
        """Топ-k документов базы знаний по совпадению слов с запросом."""
        q = Counter(_tokens(query))
        scored = []
        for doc in self.knowledge:
            d = Counter(_tokens(doc))
            overlap = sum(min(q[w], d[w]) for w in q if w in d)
            if overlap:
                scored.append((overlap, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:k]]

    def build_context(self, query, k=3):
        """Собрать промпт: system prompt + релевантные знания + запрос."""
        docs = self.retrieve(query, k)
        kb = "\n".join(f"- {d}" for d in docs) or "(нет релевантных знаний)"
        return f"{self.system_prompt}\n\n# База знаний\n{kb}\n\n# Запрос\n{query}"


if __name__ == "__main__":
    proj = Project(
        name="support-bot",
        system_prompt="Ты ассистент поддержки. Отвечай кратко и по делу.",
        knowledge=[
            "Возврат возможен в течение 14 дней.",
            "Гарантия на электронику — 12 месяцев.",
            "Доставка по городу 1-2 дня.",
        ],
    )
    print(proj.build_context("сколько дней на возврат?", k=1))
