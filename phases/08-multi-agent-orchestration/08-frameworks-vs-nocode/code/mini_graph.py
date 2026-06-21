"""Оркестрация: мини-граф процесса (как LangGraph) — Build It 8.4.

Без зависимостей. Фреймворки оркестрации (LangGraph и т.п.) — это граф: узлы-шаги,
рёбра-переходы, условные ветвления и циклы поверх общего состояния. Собираем
уменьшенную версию, чтобы понять, что no-code/фреймворк делают под капотом.
В USE IT — тот же процесс в LangGraph / n8n.
"""

END = "__end__"


class Graph:
    """Граф процесса: узлы (fn над состоянием) + рёбра (обычные и условные)."""

    def __init__(self):
        self.nodes = {}
        self.edges = {}        # node -> next node
        self.cond = {}         # node -> router(state) -> next node
        self.entry = None

    def add_node(self, name, fn):
        self.nodes[name] = fn
        return self

    def set_entry(self, name):
        self.entry = name
        return self

    def add_edge(self, src, dst):
        self.edges[src] = dst
        return self

    def add_conditional(self, src, router):
        self.cond[src] = router
        return self

    def run(self, state, max_steps=100):
        """Прогнать состояние по графу от entry до END. Возвращает (state, путь)."""
        node, path = self.entry, []
        for _ in range(max_steps):
            if node == END or node is None:
                break
            path.append(node)
            state = self.nodes[node](state)
            if node in self.cond:
                node = self.cond[node](state)
            elif node in self.edges:
                node = self.edges[node]
            else:
                node = END
        return state, path


if __name__ == "__main__":
    g = Graph()
    g.add_node("inc", lambda s: {**s, "n": s["n"] + 1})
    g.add_node("done", lambda s: {**s, "status": "готово"})
    g.set_entry("inc")
    # цикл: пока n < 3 — обратно в inc, иначе в done
    g.add_conditional("inc", lambda s: "inc" if s["n"] < 3 else "done")
    g.add_edge("done", END)
    state, path = g.run({"n": 0})
    print("итог:", state, "| путь:", path)
