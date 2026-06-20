# Урок 0.2 · Аккаунты, тарифы, API-ключи, окружение

**Фаза 0 — Setup & Tooling** · **Результат фазы:** Настроить окружение, ключи и агента; осознанно выбрать модель под задачу.
<!-- **Requires:** платный API-ключ (Anthropic / OpenAI / Google) — только для блока USE IT -->

> **MOTTO.** Ключи — в `.env`, секреты — не в коде, окружение — воспроизводимо.

## PROBLEM

Первый запрос к API спотыкается не о модель, а о быт: где взять ключ, куда его положить, почему `ANTHROPIC_API_KEY` «не виден», и как не закоммитить секрет в git. Захардкоженный ключ в коде утекает в репозиторий и в историю; «работает у меня» рушится на другой машине без зафиксированного окружения.

## CONCEPT

Здоровое окружение состоит из трёх вещей:

```
venv (изоляция)  +  .env (секреты)  +  .env.example (контракт)
        │                  │                    │
   свои пакеты      ключи вне кода        что нужно завести
   не ломают         и вне git           (без значений)
   систему         (.gitignore)
```

- **venv** — изолированный Python, чтобы зависимости урока не конфликтовали с системными.
- **.env** — файл `KEY=VALUE` с секретами; он **в `.gitignore`**, в репозиторий не попадает.
- **.env.example** — тот же список ключей без значений; коммитится как контракт «что нужно завести».

## BUILD IT

Парсер `.env` и валидатор ключей с нуля, без зависимостей и **без сети**: [`code/envcheck.py`](../code/envcheck.py).

- `parse_env(text)` — разбирает `.env` (комментарии, `export`, кавычки, inline-комментарии);
- `validate(env, required)` — проверяет, что нужные ключи заданы, не плейсхолдеры и похожи на ключ по префиксу.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python code/envcheck.py
pytest code -q
```

Валидатор офлайн ловит типовые ошибки (нет ключа, остался `your-key-here`, неверный префикс) до того, как ты потратишь время на отлов 401 от API.

## USE IT

Заведи аккаунты и ключи в консолях провайдеров, затем сделай первый реальный запрос:

- **Anthropic Console** → `ANTHROPIC_API_KEY` (`sk-ant-…`)
- **OpenAI Platform** → `OPENAI_API_KEY` (`sk-…`)
- **Google AI Studio** → `GOOGLE_API_KEY`

```python
import os
# ключи берутся из окружения, а не из кода
# Anthropic
from anthropic import Anthropic
print(Anthropic().messages.create(model="claude-haiku-4-5", max_tokens=50,
    messages=[{"role": "user", "content": "Привет одним словом"}]).content[0].text)

# OpenAI
from openai import OpenAI
print(OpenAI().responses.create(model="gpt-5.x", input="Привет одним словом").output_text)

# Google
from google import genai
print(genai.Client().models.generate_content(
    model="gemini-2.x-flash", contents="Привет одним словом").text)
```

Бери для проверки **самую дешёвую** модель (Haiku / Flash) — первый запрос не должен стоить дорого.

## SHIP IT

**Артефакт:** Готовое окружение + проверочный скрипт → [`outputs/env-starter/`](../outputs/env-starter/)

Drop-in набор для любого проекта курса: `.env.example` (контракт ключей), `check_env.py` (самодостаточный валидатор без зависимостей) и `.gitignore`-строка для `.env`. Копируешь в новый проект — и окружение проверяемо с первой минуты.

## Материалы

- [Anthropic — Quickstart](https://docs.anthropic.com/en/docs/quickstart) — ключ и первый запрос к Claude.
- [OpenAI — Developer quickstart](https://platform.openai.com/docs/quickstart) — ключ и первый запрос к OpenAI.
- [Gemini — API keys](https://ai.google.dev/gemini-api/docs/api-key) — получение и хранение ключа Google.
- [python-dotenv](https://pypi.org/project/python-dotenv/) — загрузка `.env` в окружение (12-factor).

---
**Часы:** ~2 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
