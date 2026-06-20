# Урок 2.3 · Декомпозиция и итеративное уточнение

**Фаза 2 — Промпт-инжиниринг** · **Результат фазы:** Писать воспроизводимые промпты и измерять их качество через eval-harness.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** Сложную задачу не «промптят» одним мегапромптом, а разбивают на цепочку шагов.

## PROBLEM

Один огромный промпт «сделай всё сразу» ненадёжен: модель роняет шаги, путает порядок, а отладить «почему плохо» невозможно — всё слиплось. Сложные процессы (исследование → черновик → правка → формат) требуют **декомпозиции**: цепочки промптов, где выход одного шага — вход следующего.

## CONCEPT

```
вход → [шаг 1] → [шаг 2] → [шаг 3] → итог
          │ каждый шаг = отдельный промпт с одной целью
          ▼ выход шага виден и проверяем (трейс)
   типовые цепочки: Extract → Transform → Analyze → Format
                    Generate → Review → Improve  (self-correction)
```

Плюсы: **точность** (каждый шаг — в фокусе), **ясность** (простые инструкции), **трассируемость** (видно, где сломалось). Это прямой мост к агентам (Фаза 7).

## BUILD IT

Раннер цепочки промптов с трейсом: [`code/prompt_chain.py`](../code/prompt_chain.py).

- `ChainStep(name, fn)` — шаг цепочки;
- `run_chain(steps, initial, trace)` — прогоняет значение через шаги, возвращает `(итог, история)`.

```bash
python code/prompt_chain.py
pytest code -q
```

Шаги здесь — детерминированные функции (офлайн); цепочка `extract → sum → format` решает то, что один шаг не может. Виден трейс каждого перехода — это и есть отлаживаемость.

## USE IT

В проде каждый `ChainStep.fn` — отдельный вызов модели; выход подаётся в следующий промпт:

```python
def step_llm(instruction):
    def fn(value):
        prompt = f"{instruction}\n\nВход:\n{value}"
        return Anthropic().messages.create(model="claude-sonnet-4-6", max_tokens=500,
            messages=[{"role": "user", "content": prompt}]).content[0].text
        # OpenAI: OpenAI().responses.create(model="gpt-5.x", input=prompt).output_text
        # Google: genai.Client().models.generate_content(model="gemini-2.x-flash", contents=prompt).text
    return fn

chain = [ChainStep("outline", step_llm("Составь план")),
         ChainStep("draft",   step_llm("Напиши черновик по плану")),
         ChainStep("edit",    step_llm("Отредактируй: короче и яснее"))]
```

Независимые шаги можно гонять параллельно; последовательно — только когда есть зависимость.

## SHIP IT

**Артефакт:** Промпт-цепочка под рабочий процесс → [`outputs/prompt-chain.md`](../outputs/prompt-chain.md)

Шаблон цепочки (этапы, что подаётся между шагами, где точки проверки) под твой реальный процесс. Дальше: агентный цикл reason→act→observe — урок 7.1.

## Материалы

- [Anthropic — Chain complex prompts](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/chain-prompts) — когда и как дробить задачу на цепочку.
- [Wei et al., 2022 — Chain-of-Thought](https://arxiv.org/abs/2201.11903) — пошаговое рассуждение как основа декомпозиции.
- [Anthropic — Prompting best practices](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices) — паттерн self-correction (generate → review → improve).

---
**Часы:** ~3 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
