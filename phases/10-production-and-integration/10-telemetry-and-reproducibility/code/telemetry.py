"""Телеметрия и воспроизводимость — Build It для урока 10.3.

Без зависимостей. Считаем токены и стоимость в разрезе процессов (телеметрия) и
фиксируем конфигурацию запуска (модель, параметры, версия промпта) так, чтобы
прогон можно было воспроизвести — одинаковый конфиг даёт одинаковый «отпечаток».
"""
import hashlib
import json
from dataclasses import dataclass, asdict, field


class Telemetry:
    """Учёт токенов и стоимости по процессам."""

    def __init__(self):
        self.events = []

    def record(self, process, tokens_in, tokens_out, cost):
        self.events.append({"process": process, "tokens_in": tokens_in,
                            "tokens_out": tokens_out, "cost": cost})

    def by_process(self):
        out = {}
        for e in self.events:
            agg = out.setdefault(e["process"], {"tokens_in": 0, "tokens_out": 0, "cost": 0.0})
            agg["tokens_in"] += e["tokens_in"]
            agg["tokens_out"] += e["tokens_out"]
            agg["cost"] = round(agg["cost"] + e["cost"], 6)
        return out

    def total_cost(self):
        return round(sum(e["cost"] for e in self.events), 6)


@dataclass
class RunConfig:
    """Конфиг прогона для воспроизводимости."""
    model: str
    temperature: float = 0.0
    prompt_version: str = "v1"
    seed: int = 0

    def fingerprint(self):
        """Стабильный отпечаток конфига: одинаковый конфиг → одинаковый хэш."""
        blob = json.dumps(asdict(self), sort_keys=True).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()[:12]


if __name__ == "__main__":
    tel = Telemetry()
    tel.record("summarize", 1000, 200, 0.005)
    tel.record("summarize", 800, 150, 0.004)
    tel.record("classify", 300, 10, 0.0003)
    print("по процессам:", tel.by_process())
    print("итого $:", tel.total_cost())

    a = RunConfig("sonnet-4.6", temperature=0.0, prompt_version="v1")
    b = RunConfig("sonnet-4.6", temperature=0.7, prompt_version="v1")
    print("fp(a):", a.fingerprint(), "| fp(a2):", RunConfig("sonnet-4.6").fingerprint())
    print("fp(b) отличается:", a.fingerprint() != b.fingerprint())
