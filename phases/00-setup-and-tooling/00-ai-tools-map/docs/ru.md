# Урок 0.1 · Карта инструментов ИИ 2026

**Фаза 0 — Setup & Tooling** · **Результат фазы:** Настроить окружение, ключи и агента; осознанно выбрать модель под задачу.

> **MOTTO.** Не «одна модель на всё», а правильная модель под конкретную задачу.

## PROBLEM

Моделей и инструментов в 2026 — десятки, и легко свалиться в две крайности: гонять всё через самую дорогую модель «на всякий случай» (счёт за API улетает в космос) или через самую дешёвую (качество проседает на сложном). Без карты «что под что» выбор превращается в гадание, а различия между Claude, GPT, Gemini, Copilot и Perplexity сливаются в кашу.

## CONCEPT

Инструменты делятся на два слоя:

- **Модели через API** — то, что вызываешь кодом (Claude, GPT, Gemini). Платишь за токены, выбираешь под задачу.
- **Готовые продукты** — обёртки вокруг моделей под сценарий: Copilot (код в IDE/M365), Perplexity (поиск с источниками), чат-интерфейсы.

Ключевая ось выбора модели — **сложность × объём × цена × задержка**:

```
       дорого/умно
            ▲
   Opus 4.8 │ сложное рассуждение, код, анализ
 Sonnet 4.6 │ рабочая лошадка
   GPT-5.x  │ универсальные задачи
  Haiku 4.5 │ рутина, черновики, извлечение
Gemini Flash│ массовое, классификация
DeepSeek V4 │ дёшево + reasoning + open-weight (self-host)
            └──────────────► дёшево/быстро/массово
```

Правило: бери **самую дешёвую модель, которая справляется**, и эскалируй вверх только когда качество не дотягивает (мост к Фазе 9 — маршрутизация и FinOps).

Отдельная ось — **открытость весов**: закрытые API (Claude/GPT/Gemini) vs **open-weight** (DeepSeek под MIT, Llama, Qwen, Mistral), которые можно запустить у себя. Open-weight решает приватность/суверенитет данных (мост к Фазе 11), но self-host выгоден не по цене, а ради контроля.

> **Врезка: AI Fluency (4D).** Чтобы работать с ИИ осознанно, держи в голове четыре компетенции (Anthropic Academy): **Delegation** — что отдать ИИ, а что оставить человеку; **Description** — как описать задачу и поведение модели; **Discernment** — как критически оценить результат; **Diligence** — ответственность, прозрачность, проверка. Эти 4D проходят сквозь весь курс: Description ≈ Фаза 2, Discernment ≈ eval (2.5) и фактчекинг (11.2), Diligence ≈ guardrails (7.3) и этика (Фаза 11). См. [глоссарий](../../../glossary/terms.md) и курс AI Fluency.

## BUILD IT

Реестр моделей и рекомендатор «задача → модель» с нуля, без зависимостей: [`code/model_map.py`](../code/model_map.py).

- `REGISTRY` — модели с ценой входа/выхода, тиром и сильными сторонами;
- `recommend(task)` — по профилю задачи (`complexity`, `high_volume`, `needs_code`, `budget_sensitive`) возвращает модель и обоснование;
- `estimate_cost(model, n_in, n_out)` — прикидка стоимости вызова.

```bash
python code/model_map.py
pytest code -q
```

Демо показывает суть: простое+массовое → Gemini Flash, обычное → Sonnet, сложное/код → Opus.

## USE IT

Прогони **один и тот же запрос** через разные инструменты и сравни ответ, скорость и уместность:

- **Claude** (Opus 4.8 / Mythos) — сложное рассуждение, длинный контекст, код;
- **GPT-5.x** — универсальный baseline;
- **Gemini** — массовые задачи, мультимодальность, дешёвый Flash;
- **Copilot** — код прямо в IDE и в M365;
- **Perplexity** — вопросы, где нужен поиск с источниками.

Вызов модели кодом одинаков по форме у всех провайдеров (детали — в уроке 0.2):

```python
# Anthropic
from anthropic import Anthropic
Anthropic().messages.create(model="claude-opus-4-8", max_tokens=300,
    messages=[{"role": "user", "content": "Сравни 2 подхода к кэшированию"}])

# OpenAI
from openai import OpenAI
OpenAI().responses.create(model="gpt-5.x", input="Сравни 2 подхода к кэшированию")

# Google
from google import genai
genai.Client().models.generate_content(model="gemini-2.x-flash",
    contents="Сравни 2 подхода к кэшированию")
```

## SHIP IT

**Артефакт:** Личная матрица «задача → модель» → [`outputs/task-to-model-matrix.md`](../outputs/task-to-model-matrix.md)

Заполняешь под свои реальные задачи (какую модель берёшь и почему), а `recommend()` из Build It даёт стартовую рекомендацию. Матрица возвращается в Фазе 9, когда будем строить автоматический роутер.

## Материалы

- [Claude models overview](https://platform.claude.com/docs/en/about-claude/models/overview) — официальная карта моделей Anthropic и их сильные стороны.
- [OpenAI API pricing](https://openai.com/api/pricing/) — актуальные цены моделей OpenAI за токены.
- [Gemini API — models](https://ai.google.dev/gemini-api/docs) — модели Google и когда брать Flash.
- [DeepSeek — Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing) — дешёвый open-weight вариант (V4-Flash/Pro).
- [Anthropic Academy — AI Fluency (4D)](https://anthropic.skilljar.com/ai-fluency-framework-foundations) — рамка Delegation/Description/Discernment/Diligence: как осознанно работать с ИИ.

---
**Часы:** ~2 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
