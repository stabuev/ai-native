# Урок 7.6 · Realtime и голосовые агенты

**Фаза 7 — Agent Engineering** · **Результат фазы:** Собрать надёжного агента с памятью, планированием, human-in-the-loop и guardrails.
<!-- **Requires:** платный API-ключ (Realtime/Live) — только для блока USE IT -->

> **MOTTO.** Голосовой агент — это поток и право перебить: ответ идёт по чанкам, пользователь может вмешаться.

## PROBLEM

Чат-агент отвечает «целиком», голосовой — иначе: критична **низкая задержка** (TTFT), ответ идёт **потоком** (по аудио-чанкам), и пользователь может **перебить** (barge-in) — тогда текущий ответ надо оборвать. Без модели этого цикла realtime-агент ощущается «тормозным» и «глухим».

## CONCEPT

```
аудио пользователя ──► VAD (детект речи) ──► агент
                                              │ стримит ответ по токенам
       barge-in (пользователь заговорил) ──► отменить текущий ответ
                                              │
                              TTFT — ключевая метрика (время до 1-го токена)
```

Два отличия от чат-цикла (7.1): **стриминг вывода** и **прерываемость**. Управление турами (кто говорит) — сердце realtime.

## BUILD IT

Турновый streaming-цикл с barge-in, без зависимостей: [`code/streaming_loop.py`](../code/streaming_loop.py).

- `StreamingAgent.respond(tokens, interrupt_after)` — стрим ответа; перебивание обрывает турн и ставит state `interrupted`;
- `first_token_latency(timeline)` — TTFT.

```bash
python code/streaming_loop.py
pytest code -q
```

Тест: без перебивания — полный ответ (`idle`); barge-in после N токенов — частичный ответ и состояние `interrupted`. Это и есть управление турами.

## USE IT

Готовые realtime/voice API (мульти-провайдер):

- **OpenAI Realtime API** — speech-to-speech одной моделью (низкая задержка), WebRTC/WebSocket/SIP, VAD + автоматическое прерывание, tool use, телефония.
- **Gemini Live API** — двунаправленный WebSocket, аудио/видео/текст, barge-in, 70+ языков, live-перевод, function calling.
- Паттерн: VAD ловит речь → стрим ответа → barge-in отменяет текущий ответ (ровно как наш `interrupt_after`); для клиента — ephemeral tokens (безопасность).

## SHIP IT

**Артефакт:** Голосовой/realtime агент-демо → [`outputs/streaming_loop.py`](../outputs/streaming_loop.py)

Каркас турнового стрима с barge-in — подставляешь реальный VAD и Realtime/Live API. Связь с 7.1 (agent loop), 7.3 (guardrails на голосовых действиях), 10.2 (латентность как метрика).

## Материалы

- [OpenAI — Realtime API](https://developers.openai.com/api/docs/guides/realtime) — speech-to-speech, прерывания, транспорты.
- [Gemini — Live API](https://ai.google.dev/gemini-api/docs/live-api) — realtime аудио/видео, barge-in, перевод.
- [OpenAI — Voice agents](https://developers.openai.com/api/docs/guides/voice-agents) — сборка голосового агента.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
