"""Интеграция в рабочие пакеты: безопасное встраивание ИИ — Build It для урока 10.1.

Без зависимостей. Встраивая ИИ в существующий процесс, нужны две вещи: фича-флаг
(можно мгновенно выключить) и fallback (если модель упала или выключена — процесс
не падает, а деградирует мягко). Так ИИ становится заменяемой деталью пайплайна.
"""


class AIFeature:
    """Обёртка над ИИ-шагом: фича-флаг + graceful fallback."""

    def __init__(self, fn, fallback, enabled=True):
        self.fn = fn                 # вызов модели (в проде)
        self.fallback = fallback     # детерминированный запасной путь
        self.enabled = enabled

    def run(self, x):
        if not self.enabled:
            return self.fallback(x)          # фича выключена — старый путь
        try:
            return self.fn(x)
        except Exception:                     # noqa: BLE001 — прод не должен падать из-за ИИ
            return self.fallback(x)


def run_pipeline(steps, x):
    """Прогнать значение через шаги пайплайна (ИИ — один из шагов)."""
    for step in steps:
        x = step(x)
    return x


if __name__ == "__main__":
    def ai_summary(text):
        if "ошибк" in text:                       # стем: ловит «ошибка/ошибкой/...»
            raise RuntimeError("модель недоступна")
        return f"AI-саммари: {text[:20]}..."

    def naive_summary(text):
        return f"первые слова: {' '.join(text.split()[:3])}"

    feat = AIFeature(ai_summary, naive_summary, enabled=True)
    print(feat.run("длинный текст для краткого пересказа"))     # ИИ
    print(feat.run("текст с ошибкой внутри"))                   # упал → fallback
    feat.enabled = False
    print(feat.run("любой текст"))                              # выключено → fallback
