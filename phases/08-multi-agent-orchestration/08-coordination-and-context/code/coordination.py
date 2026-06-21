"""Координация и контекст — Build It для урока 8.3.

Без зависимостей. Несколько агентов работают над общим состоянием (blackboard):
читают и пишут разделяемый контекст. Главная опасность мульти-агентности —
конфликты записи; здесь они детектируются. Так оркестрация (8.1) и A2A (8.2)
превращаются в связный процесс с передачей состояния.
"""


class SharedContext:
    """Общий контекст (blackboard) с отслеживанием авторов и конфликтов записи."""

    def __init__(self):
        self.data = {}
        self.writers = {}
        self.conflicts = []

    def write(self, key, value, agent):
        # конфликт: другой агент уже записал в этот ключ ДРУГОЕ значение
        if key in self.data and self.writers[key] != agent and self.data[key] != value:
            self.conflicts.append({
                "key": key, "old": self.data[key], "new": value,
                "by": agent, "prev_by": self.writers[key],
            })
        self.data[key] = value
        self.writers[key] = agent

    def read(self, key, default=None):
        return self.data.get(key, default)


def run_process(steps, ctx=None):
    """steps: list[(agent_name, fn(ctx))]. Прогоняет агентов над общим контекстом."""
    ctx = ctx or SharedContext()
    for name, fn in steps:
        fn(ctx, name)
    return ctx


if __name__ == "__main__":
    def researcher(ctx, me):
        ctx.write("facts", ["A", "B"], me)

    def writer(ctx, me):
        ctx.write("draft", f"черновик по {len(ctx.read('facts'))} фактам", me)

    def rogue(ctx, me):
        ctx.write("facts", ["X"], me)            # перезапишет facts — конфликт

    ctx = run_process([("researcher", researcher), ("writer", writer), ("rogue", rogue)])
    print("data:", ctx.data)
    print("conflicts:", ctx.conflicts)
