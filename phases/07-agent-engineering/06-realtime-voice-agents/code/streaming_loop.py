"""Realtime и голосовые агенты: турновый streaming-цикл с barge-in — Build It 7.6.

Без зависимостей. Голосовой/realtime агент отличается от чат-агента двумя вещами:
ответ идёт ПОТОКОМ (по токенам/чанкам) и пользователь может перебить (barge-in) —
тогда текущий ответ обрывается. Здесь моделируем этот цикл детерминированно.
В USE IT — OpenAI Realtime / Gemini Live (аудио, низкая задержка).
"""


class StreamingAgent:
    """Стримит ответ по токенам; barge-in (перебивание) обрывает текущий турн."""

    def __init__(self):
        self.state = "idle"          # idle | speaking | interrupted
        self.transcript = []         # завершённые/прерванные реплики

    def respond(self, tokens, interrupt_after=None):
        """Произнести ответ потоком. interrupt_after=N → пользователь перебил после N токенов."""
        self.state = "speaking"
        said = []
        for i, tok in enumerate(tokens):
            if interrupt_after is not None and i >= interrupt_after:
                self.state = "interrupted"          # barge-in: бросаем остаток
                self.transcript.append({"said": said, "interrupted": True})
                return said
            said.append(tok)
        self.state = "idle"
        self.transcript.append({"said": said, "interrupted": False})
        return said


def first_token_latency(timeline):
    """Задержка до первого токена (TTFT) — ключевая метрика realtime."""
    return timeline[0] if timeline else None


if __name__ == "__main__":
    agent = StreamingAgent()
    print("полный ответ:", agent.respond(["при", "вет", "как", "дела"]))
    print("state:", agent.state)
    print("перебили:", agent.respond(["я", "сейчас", "расскажу", "длинно"], interrupt_after=2))
    print("state:", agent.state)
    print("TTFT:", first_token_latency([0.18, 0.05, 0.05]))
