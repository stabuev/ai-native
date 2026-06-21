"""embedded_assistant.py — артефакт урока 10.3: ИИ, встроенный в рабочий процесс.

Самодостаточно, без зависимостей. Объединяет Фазу 10: фича-флаг + fallback (10.1),
логирование вызовов (10.2), телеметрия токенов/стоимости и fingerprint конфига (10.3).
В проде `_call_model` заменяется реальным вызовом API.

Запуск:  python embedded_assistant.py
"""
import hashlib
import json
from dataclasses import dataclass, asdict

PRICES = {"sonnet-4.6": (3.0, 15.0), "haiku-4.5": (1.0, 5.0)}      # $/1M (вход, выход)


@dataclass
class RunConfig:
    model: str = "sonnet-4.6"
    temperature: float = 0.0
    prompt_version: str = "v1"

    def fingerprint(self):
        blob = json.dumps(asdict(self), sort_keys=True).encode()
        return hashlib.sha256(blob).hexdigest()[:12]


class EmbeddedAssistant:
    """ИИ-шаг процесса: флаг + fallback + лог + телеметрия."""

    def __init__(self, config: RunConfig, enabled=True):
        self.config = config
        self.enabled = enabled
        self.log = []           # вызовы (мониторинг)
        self.telemetry = []     # токены/стоимость (FinOps)

    def _cost(self, n_in, n_out):
        p_in, p_out = PRICES[self.config.model]
        return round((n_in * p_in + n_out * p_out) / 1e6, 6)

    def _call_model(self, text):
        if "ошибк" in text.lower():
            raise RuntimeError("модель недоступна")
        n_in, n_out = len(text.split()) * 2, 30
        return f"саммари: {text[:30]}...", n_in, n_out

    def _fallback(self, text):
        return "первые слова: " + " ".join(text.split()[:3])

    def run(self, text, process="summarize"):
        if not self.enabled:
            return self._fallback(text)
        try:
            answer, n_in, n_out = self._call_model(text)
            cost = self._cost(n_in, n_out)
            self.log.append({"process": process, "status": "ok", "config": self.config.fingerprint()})
            self.telemetry.append({"process": process, "tokens_in": n_in,
                                   "tokens_out": n_out, "cost": cost})
            return answer
        except Exception as e:                                  # noqa: BLE001
            self.log.append({"process": process, "status": "error", "error": str(e)})
            return self._fallback(text)

    def total_cost(self):
        return round(sum(t["cost"] for t in self.telemetry), 6)


if __name__ == "__main__":
    asst = EmbeddedAssistant(RunConfig(model="sonnet-4.6", prompt_version="v3"))
    print(asst.run("длинный отчёт для краткого пересказа команды"))
    print(asst.run("текст с ошибкой"))            # упал → fallback, залогировано
    print("config fp:", asst.config.fingerprint())
    print("total cost:", asst.total_cost())
    print("log:", asst.log)
