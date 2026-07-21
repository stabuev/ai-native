"""multi_agent_process.py — артефакт урока 8.3: сквозной мульти-агентный процесс.

Самодостаточно, без зависимостей. Объединяет Фазу 8: оркестратор раздаёт роли
субагентам, субагенты пишут в общий контекст (с детекцией конфликтов), lead сводит
результат. В проде субагенты — это LLM-агенты (Claude subagents / Agent SDK).

Запуск:  python multi_agent_process.py
"""


class SharedContext:
    """Общий blackboard с авторами записей и детекцией конфликтов."""

    def __init__(self):
        self.data, self.writers, self.conflicts = {}, {}, []

    def write(self, key, value, agent):
        if key in self.data and self.writers[key] != agent and self.data[key] != value:
            self.conflicts.append({"key": key, "by": agent, "prev_by": self.writers[key]})
        self.data[key] = value
        self.writers[key] = agent

    def read(self, key, default=None):
        return self.data.get(key, default)


# --- субагенты-роли (в проде — LLM-агенты со своим контекстом) ---
def researcher(ctx, me):
    ctx.write("facts", ["возврат 14 дней", "гарантия 12 мес"], me)


def writer(ctx, me):
    facts = ctx.read("facts", [])
    ctx.write("draft", f"Памятка по {len(facts)} пунктам: " + "; ".join(facts), me)


def reviewer(ctx, me):
    draft = ctx.read("draft", "")
    ctx.write("review", "ок" if "14 дней" in draft else "проверить факты", me)


def orchestrate(steps):
    """Lead: прогоняет субагентов над общим контекстом и сводит результат."""
    ctx = SharedContext()
    for name, fn in steps:
        fn(ctx, name)
    return {"result": ctx.read("draft"), "review": ctx.read("review"),
            "conflicts": ctx.conflicts}


if __name__ == "__main__":
    out = orchestrate([("researcher", researcher), ("writer", writer), ("reviewer", reviewer)])
    print("Результат :", out["result"])
    print("Ревью     :", out["review"])
    print("Конфликты :", out["conflicts"] or "нет")
