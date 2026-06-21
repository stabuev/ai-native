# Урок 1.2 · Контекстное окно и inference

**Фаза 1 — Как работают LLM** · **Результат фазы:** Объяснить токены, контекст и inference; собрать токен-бюджетер; отличать надёжный ответ от галлюцинации.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** Inference — это не «один ответ», а цикл: предскажи токен, допиши, повтори.

## PROBLEM

Кажется, что модель «читает вопрос и пишет ответ» целиком. На самом деле она генерирует **по одному токену за шаг**, каждый раз заново глядя на весь контекст. Не понимая этого, нельзя объяснить, почему ответ приходит постепенно (стриминг), почему «забывается» начало длинного диалога и что вообще значит «контекст 200K токенов».

## CONCEPT

Генерация — авторегрессивный цикл вокруг **контекстного окна** (сколько последних токенов модель видит):

```
prompt ─► [ контекстное окно ] ─► P(next token) ─► argmax/sample ─► токен
              ▲                                                       │
              └──────────────── допишем токен в контекст ◄───────────┘
                         (что вышло за окно — «исчезает»)
```

Два следствия: **(1)** ответ строится пошагово — поэтому возможен стриминг; **(2)** окно конечно — выходит за него история, и модель её больше не «видит» (отсюда — бюджет контекста).

**Reasoning-модели** (Claude extended thinking, DeepSeek V4 thinking-mode, o-серия) добавляют к этому циклу скрытый этап «размышления»: перед ответом генерируются *thinking-токены*, за которые ты тоже платишь. Это даёт качество на сложных задачах, но увеличивает и стоимость, и задержку — учитывай в бюджете (Фаза 9).

## BUILD IT

Учебный inference-loop с контекстным окном, без зависимостей: [`code/inference_loop.py`](../code/inference_loop.py).

- `train_ngram(corpus, order)` — игрушечная модель: n-граммы с backoff;
- `next_token_probs(model, context)` — распределение следующего токена по самому длинному совпавшему суффиксу;
- `generate(model, prompt, max_tokens, window)` — жадная авторегрессия; `window` ограничивает видимый контекст.

```bash
python code/inference_loop.py
pytest code -q
```

Ключевая демонстрация: одинаковый prompt при разном `window` даёт **разный** результат — это и есть эффект контекстного окна.

## USE IT

Тот же цикл — у реальной модели, но виден через **стриминг** (токены приходят по мере генерации). Мульти-провайдер:

```python
# Anthropic
from anthropic import Anthropic
with Anthropic().messages.stream(model="claude-opus-4-8", max_tokens=200,
    messages=[{"role": "user", "content": "Объясни inference в 3 предложениях"}]) as s:
    for text in s.text_stream:
        print(text, end="")

# OpenAI
from openai import OpenAI
for ev in OpenAI().responses.create(model="gpt-5.x",
        input="Объясни inference в 3 предложениях", stream=True):
    if ev.type == "response.output_text.delta":
        print(ev.delta, end="")

# Google
from google import genai
for chunk in genai.Client().models.generate_content_stream(
        model="gemini-2.x-flash", contents="Объясни inference в 3 предложениях"):
    print(chunk.text, end="")
```

Каждый «delta» — это один (или несколько) только что сгенерированных токенов: тот самый цикл из Build It, но в проде.

## SHIP IT

**Артефакт:** Памятка по бюджету контекста → [`outputs/context-budget-cheatsheet.md`](../outputs/context-budget-cheatsheet.md)

Короткая шпаргалка: из чего складывается контекст (system + история + RAG + ответ), что обрезать первым, как не упереться в окно. Связка с `prompt-token-budgeter` из 1.1 и с Фазой 4 (контекст-инжиниринг).

## Материалы

- [Anthropic — Streaming Messages](https://docs.anthropic.com/en/api/messages-streaming) — как устроен стриминг (SSE) у Claude.
- [OpenAI — Streaming responses](https://platform.openai.com/docs/guides/streaming-responses) — стриминг в Responses API.
- [Gemini — Quickstart](https://ai.google.dev/gemini-api/docs/quickstart) — первый вызов и стриминг у Google.

---
**Часы:** ~3 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
