"""Деплой и мониторинг: логирование вызовов — Build It для урока 10.2.

Без зависимостей. В проде каждый вызов модели логируется структурно (модель,
латентность, статус, ошибка), а поверх лога считаются метрики здоровья: доля
ошибок и перцентили латентности. Без этого «работает/не работает» — вслепую.
"""


class CallLogger:
    """Структурный лог вызовов + базовые метрики мониторинга."""

    def __init__(self):
        self.calls = []

    def log(self, model, latency_ms, ok=True, error=None):
        self.calls.append({"model": model, "latency_ms": latency_ms,
                           "ok": ok, "error": error})

    def error_rate(self):
        if not self.calls:
            return 0.0
        return round(sum(1 for c in self.calls if not c["ok"]) / len(self.calls), 3)

    def latency_percentile(self, p=95):
        """Приблизительный перцентиль латентности (nearest-rank)."""
        if not self.calls:
            return 0.0
        values = sorted(c["latency_ms"] for c in self.calls)
        k = max(0, min(len(values) - 1, round(p / 100 * len(values)) - 1))
        return values[k]

    def recent_errors(self, n=5):
        return [c for c in self.calls if not c["ok"]][-n:]


if __name__ == "__main__":
    log = CallLogger()
    for ms, ok in [(120, True), (300, True), (90, True), (1500, False), (200, True)]:
        log.log("sonnet-4.6", ms, ok=ok, error=None if ok else "timeout")
    print("error_rate:", log.error_rate())
    print("p95 latency:", log.latency_percentile(95))
    print("errors:", log.recent_errors())
