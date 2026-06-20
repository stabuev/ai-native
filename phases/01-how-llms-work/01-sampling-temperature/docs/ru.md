# Урок 1.3 · Сэмплирование, температура, детерминизм

**Фаза 1 — Как работают LLM** · **Результат фазы:** Объяснить токены, контекст и inference; собрать токен-бюджетер; отличать надёжный ответ от галлюцинации.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** Модель выдаёт распределение, а не ответ; температура и top-p решают, как из него выбрать.

## PROBLEM

«Почему один и тот же промпт даёт то одинаковые, то разные ответы?» и «как сделать вывод воспроизводимым?» — без понимания сэмплинга это магия. На каждом шаге модель отдаёт **распределение вероятностей** по токенам; то, насколько ответ детерминирован или креативен, определяют параметры выбора: `temperature`, `top_k`, `top_p`.

## CONCEPT

```
logits ──softmax(T)──► вероятности ──фильтр top-k / top-p──► выбор токена
            │                              │
   T→0: пик на argmax (детерминизм)   top-k: оставить k лучших
   T↑ : распределение «плоское»       top-p: минимум токенов с суммой ≥ p (nucleus)
```

- **temperature** — «сглаживает» (↑) или «заостряет» (↓) распределение. `T=0` → всегда argmax → детерминизм.
- **top-k** — оставить k самых вероятных кандидатов, остальное отбросить.
- **top-p (nucleus)** — оставить минимальный набор, чья суммарная вероятность ≥ p (размер набора плавает).

## BUILD IT

Реализация softmax(T), top-k, top-p и сэмплера с нуля: [`code/sampling.py`](../code/sampling.py).

- `softmax(logits, temperature)` — распределение; `T<=0` → one-hot на argmax;
- `top_k_filter` / `top_p_filter` — отсечение хвоста + перенормировка;
- `sample(logits, temperature, top_k, top_p, rng)` — выбор индекса; с `rng=Random(seed)` воспроизводим.

```bash
python code/sampling.py
pytest code -q
```

Демо показывает: с ростом `T` растёт энтропия распределения; `T=0` и `top_k=1` дают строго argmax; один и тот же seed → один и тот же сэмпл (детерминизм).

## USE IT

Покрути параметры у реальных моделей и сравни разброс ответов (мульти-провайдер):

```python
# OpenAI — temperature 0..2
OpenAI().responses.create(model="gpt-5.x", input="Придумай слоган", temperature=0.2)
# Google — temperature/top_p в generation_config
genai.Client().models.generate_content(model="gemini-2.x-flash", contents="Придумай слоган",
    config={"temperature": 0.9, "top_p": 0.95})
```

⚠️ **Важно (2026):** у новейших Claude (**Opus 4.7+ / 4.8**) параметры `temperature`/`top_p`/`top_k` **не поддерживаются** — их передача вернёт 400, поведение задаётся промптом. Для экспериментов с сэмплингом бери модели, где они открыты (OpenAI: 0–2; Gemini; более ранние Claude — причём `temperature` и `top_p` меняют **по одному**, не вместе).

## SHIP IT

**Артефакт:** Гайд по параметрам генерации → [`outputs/generation-params-guide.md`](../outputs/generation-params-guide.md)

Шпаргалка «какой параметр под какую задачу»: когда `T=0` (извлечение, классификация, воспроизводимость), когда выше (черновики, брейншторм), как сочетать с top-p и где они вообще доступны.

## Материалы

- [Holtzman et al., 2019 — Nucleus Sampling (top-p)](https://arxiv.org/abs/1904.09751) — первоисточник top-p и почему argmax деградирует.
- [Anthropic — Messages API](https://docs.anthropic.com/en/api/messages) — параметры запроса и ограничения по моделям.
- [OpenAI — Prompt engineering best practices](https://help.openai.com/en/articles/6654000-best-practices-for-prompt-engineering-with-the-openai-api) — про temperature и выбор параметров.

---
**Часы:** ~3 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
