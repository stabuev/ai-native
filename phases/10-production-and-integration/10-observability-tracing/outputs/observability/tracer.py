"""Observability и трейсинг агентов: spans с нуля — Build It 10.4.

Без зависимостей. Чтобы отлаживать агента в проде, нужен трейс: вложенные spans
(шаг → подшаг) с длительностью и атрибутами — как в OpenTelemetry GenAI. Собираем
мини-трейсер. В USE IT — LangSmith / Langfuse / Arize поверх того же принципа.
"""
import time
from contextlib import contextmanager


class Tracer:
    """Сбор вложенных spans. clock можно подменить для воспроизводимых тестов."""

    def __init__(self, clock=None):
        self.spans = []
        self._stack = []
        self._clock = clock or time.perf_counter

    @contextmanager
    def span(self, name, **attrs):
        sp = {"name": name, "attrs": attrs,
              "parent": self._stack[-1]["name"] if self._stack else None,
              "start": self._clock()}
        self.spans.append(sp)
        self._stack.append(sp)
        try:
            yield sp
        finally:
            sp["end"] = self._clock()
            sp["duration"] = sp["end"] - sp["start"]
            self._stack.pop()

    def total_duration(self):
        """Суммарная длительность корневых spans."""
        return sum(s["duration"] for s in self.spans if s["parent"] is None)

    def slowest(self):
        """Самый долгий span (узкое место)."""
        finished = [s for s in self.spans if "duration" in s]
        return max(finished, key=lambda s: s["duration"]) if finished else None


if __name__ == "__main__":
    tr = Tracer()
    with tr.span("agent_run"):
        with tr.span("retrieve", k=3):
            time.sleep(0.01)
        with tr.span("llm_call", model="sonnet-4.6"):
            time.sleep(0.02)
    print("spans:", [(s["name"], s["parent"], round(s["duration"] * 1000)) for s in tr.spans])
    print("total ms:", round(tr.total_duration() * 1000))
    print("slowest:", tr.slowest()["name"])
