"""Оркестратор и субагенты — Build It для урока 8.1.

Без зависимостей. Оркестратор разбивает задачу и раздаёт подзадачи специализи-
рованным субагентам (по ролям), затем собирает результаты. Субагенты здесь —
детерминированные функции-роли (офлайн); в USE IT их роль играют LLM-агенты.
"""


class Orchestrator:
    """Раздаёт подзадачи субагентам по ролям и собирает результаты."""

    def __init__(self):
        self.subagents = {}

    def register(self, role, fn):
        self.subagents[role] = fn

    def delegate(self, role, task):
        if role not in self.subagents:
            raise KeyError(f"нет субагента для роли: {role}")
        return self.subagents[role](task)

    def run(self, plan):
        """plan: list[(role, task)]. Возвращает результаты по ролям (в порядке плана).

        Поздние шаги могут использовать результаты ранних через сам task.
        """
        results = {}
        for role, task in plan:
            results[role] = self.delegate(role, task)
        return results


if __name__ == "__main__":
    orch = Orchestrator()
    orch.register("researcher", lambda topic: [f"факт о {topic} #1", f"факт о {topic} #2"])
    orch.register("writer", lambda ctx: f"черновик по {len(ctx['facts'])} фактам")
    orch.register("reviewer", lambda draft: f"проверено: {draft}")

    facts = orch.delegate("researcher", "RAG")
    plan = [("writer", {"facts": facts}), ("reviewer", "черновик по 2 фактам")]
    print("facts:", facts)
    print("results:", orch.run(plan))
