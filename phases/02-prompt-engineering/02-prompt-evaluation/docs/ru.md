# Урок 2.5 · Оценка качества промптов

**Фаза 2 — Промпт-инжиниринг** · **Результат фазы:** Писать воспроизводимые промпты и измерять их качество через eval-harness.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** «Кажется, лучше» — не метрика. Промпт улучшают, измеряя на наборе кейсов.

## PROBLEM

Промпты правят «на глаз»: поменял формулировку, ответ на одном примере стал красивее — закоммитил. А на десяти других стало хуже, и ты этого не видишь. Без **eval-harness** нельзя ни сравнить две версии промпта честно, ни понять, что новая модель/параметр реально лучше. Это венец фазы: промпт-инжиниринг становится наукой, а не гаданием.

## CONCEPT

```
набор кейсов {input, expected}
        │
   prompt_fn (версия промпта / модель)
        │
     метрика(pred, expected) → score за кейс
        │
   усреднили → score версии → compare(версии) → рейтинг
```

Метрика выбирается под задачу: `exact_match` (классификация, извлечение), `contains` (есть ли нужное), LLM-as-judge (качество текста — позже). Главное — фиксированный набор кейсов и автоматическая оценка.

## BUILD IT

Mini eval-harness с метриками и сравнением версий: [`code/eval_harness.py`](../code/eval_harness.py).

- `exact_match`, `contains` — метрики `(pred, expected) → [0..1]`;
- `evaluate(prompt_fn, cases, metric)` — прогон по кейсам → `{score, per_case}`;
- `compare(versions, cases, metric)` — рейтинг версий по убыванию качества.

```bash
python code/eval_harness.py
pytest code -q
```

Демо честно ранжирует «версии промпта»: рабочая → 1.0, угадайка → 0.0; `compare` ставит лучшую первой. Это и есть инструмент выбора.

## USE IT

В проде `prompt_fn` — вызов модели; harness прогоняет твой набор кейсов и сравнивает версии/модели (мульти-провайдер):

```python
def v_claude(x): return Anthropic().messages.create(model="claude-haiku-4-5",
    max_tokens=50, messages=[{"role": "user", "content": PROMPT.format(x=x)}]).content[0].text
def v_openai(x): return OpenAI().responses.create(model="gpt-5.x", input=PROMPT.format(x=x)).output_text
def v_gemini(x): return genai.Client().models.generate_content(
    model="gemini-2.x-flash", contents=PROMPT.format(x=x)).text

print(compare({"claude": v_claude, "openai": v_openai, "gemini": v_gemini}, CASES, metric=contains))
```

Так выбор модели и версии промпта становится измеримым (мост к Фазе 9 — цена против качества).

## SHIP IT

**Артефакт:** `prompt-eval` (skill) → [`outputs/prompt-eval/`](../outputs/prompt-eval/SKILL.md)

Переиспользуемый скилл оценки промптов: подкладываешь кейсы и версии — получаешь рейтинг. Зарегистрирован в [`.claude/skills/prompt-eval`](../../../.claude/skills/prompt-eval/SKILL.md). Это рабочая лошадка для всех последующих фаз, где надо доказать, что «стало лучше».

## Материалы

- [Anthropic — Create strong empirical evaluations](https://docs.anthropic.com/en/docs/build-with-claude/develop-tests) — как строить eval-наборы и грейдинг.
- [Anthropic — Define your success criteria](https://docs.anthropic.com/en/docs/build-with-claude/define-success) — что именно измерять.
- [anthropics/anthropic-cookbook — building_evals](https://github.com/anthropics/anthropic-cookbook/blob/main/misc/building_evals.ipynb) — практический ноутбук по evals.

---
**Часы:** ~3 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
