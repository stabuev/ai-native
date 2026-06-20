# Урок 2.2 · Few-shot и chain-of-thought

**Фаза 2 — Промпт-инжиниринг** · **Результат фазы:** Писать воспроизводимые промпты и измерять их качество через eval-harness.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** Покажи примеры — и модель поймёт формат; попроси рассуждать — и она решит сложное.

## PROBLEM

На задачах с нестандартным форматом или многошаговым рассуждением «просто спросить» даёт сбои: модель угадывает разметку, путает классы, прыгает к неверному ответу. Две дешёвые техники резко поднимают качество без дообучения — **few-shot** (примеры в промпте) и **chain-of-thought** (пошаговое рассуждение).

## CONCEPT

```
zero-shot : задача → ответ                         (модель угадывает формат)
few-shot  : пример,пример,пример → задача → ответ   (учится по образцам)
CoT       : задача → «думай по шагам» → шаги → ответ (разворачивает рассуждение)
```

- **Few-shot** задаёт формат и семантику метки примерами — особенно помогает классификации и разметке.
- **CoT** даёт модели «развернуть» промежуточные шаги — помогает арифметике и логике.

## BUILD IT

Сборщики few-shot/CoT + демонстрация ценности примеров: [`code/few_shot.py`](../code/few_shot.py).

- `format_few_shot(instruction, examples, query)` и `format_cot(instruction, query)` — построение промптов;
- `knn_predict` (few-shot аналог) против `zero_shot_predict` (без примеров) на игрушечном датасете → измеримая разница в `accuracy`.

```bash
python code/few_shot.py
pytest code -q
```

Демо численно показывает то, ради чего урок: few-shot даёт точность **1.0** против **0.5** у zero-shot на тех же данных.

## USE IT

Сравни точность с/без примеров на реальной модели (мульти-провайдер): прогони набор кейсов в трёх режимах — zero-shot, few-shot, CoT — и сравни долю верных.

```python
zero = "Классифицируй тональность: 'ужасный сервис'"
few  = format_few_shot("Классифицируй тональность.", EXAMPLES, "ужасный сервис")
cot  = format_cot("Классифицируй тональность.", "ужасный сервис")
for prompt in (zero, few, cot):
    Anthropic().messages.create(model="claude-haiku-4-5", max_tokens=100,
        messages=[{"role": "user", "content": prompt}])
    OpenAI().responses.create(model="gpt-5.x", input=prompt)
    genai.Client().models.generate_content(model="gemini-2.x-flash", contents=prompt)
```

Измерять разницу будем системно в уроке 2.5 (eval-harness).

## SHIP IT

**Артефакт:** Набор few-shot заготовок → [`outputs/few-shot-templates.md`](../outputs/few-shot-templates.md)

Готовые шаблоны few-shot и CoT под типовые задачи (классификация, извлечение, рассуждение) — подставляешь свои примеры.

## Материалы

- [Brown et al., 2020 — Language Models are Few-Shot Learners (GPT-3)](https://arxiv.org/abs/2005.14165) — откуда взялся few-shot.
- [Wei et al., 2022 — Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903) — первоисточник CoT.
- [anthropics/prompt-eng-interactive-tutorial](https://github.com/anthropics/prompt-eng-interactive-tutorial) — практические главы про примеры и пошаговое мышление.

---
**Часы:** ~3 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
