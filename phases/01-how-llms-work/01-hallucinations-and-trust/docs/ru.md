# Урок 1.4 · Галлюцинации и границы доверия

**Фаза 1 — Как работают LLM** · **Результат фазы:** Объяснить токены, контекст и inference; собрать токен-бюджетер; отличать надёжный ответ от галлюцинации.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** Модель всегда говорит уверенно — доверие нужно проверять, а не предполагать.

## PROBLEM

LLM по умолчанию старается быть полезной и **отвечает даже там, где не знает**: придумывает факты, принимает ложные предпосылки, «угадывает» неизвестное. Звучит это так же уверенно, как и правда. Без понимания, где проходит граница доверия, легко принять галлюцинацию за факт — и встроить её в работу.

## CONCEPT

Галлюцинация — не «сбой», а следствие механизма: модель предсказывает правдоподобный следующий токен, а не истину. Типовые провокаторы:

```
неотвечаемое (выдуманная сущность, будущее)  → ждём «не знаю»
ложная предпосылка («почему X из золота?»)   → ждём «оспорить предпосылку»
нормальный вопрос                            → ждём ответ по делу
```

Защита — не «верить/не верить», а **проверяемое поведение**: дать право сказать «не знаю», требовать цитат/источников, сверять ответы между прогонами и моделями.

## BUILD IT

Тест-набор проб + эвристический оценщик доверия, без зависимостей: [`code/hallucination_probes.py`](../code/hallucination_probes.py).

- `PROBES` — пробы трёх типов: `unanswerable`, `false_premise`, `answerable`;
- `evaluate_response(probe, response)` — по маркерам проверяет, корректно ли поведение (воздержался / оспорил / ответил);
- `trust_score(results)` — доля корректных реакций.

```bash
python code/hallucination_probes.py
pytest code -q
```

Оценщик намеренно простой (ищет маркеры, а не «понимает» текст) — он задаёт **что именно проверять**. Это нижняя граница, а не замена человеку.

## USE IT

Прогони один и тот же набор `PROBES` через разные модели и версии и сравни `trust_score` (мульти-провайдер):

```python
def ask_claude(p):   # Anthropic
    return Anthropic().messages.create(model="claude-opus-4-8", max_tokens=300,
        messages=[{"role": "user", "content": p["prompt"]}]).content[0].text
def ask_openai(p):   # OpenAI
    return OpenAI().responses.create(model="gpt-5.x", input=p["prompt"]).output_text
def ask_gemini(p):   # Google
    return genai.Client().models.generate_content(model="gemini-2.x-flash", contents=p["prompt"]).text

for ask in (ask_claude, ask_openai, ask_gemini):
    results = [evaluate_response(p, ask(p)) for p in PROBES]
    print(ask.__name__, "trust_score:", trust_score(results))
```

Так видно: модели по-разному держат границу доверия; «допиши: можешь сказать ‘не знаю’» в промпте заметно поднимает score.

## SHIP IT

**Артефакт:** Чек-лист доверия к ответу → [`outputs/trust-checklist.md`](../outputs/trust-checklist.md)

Практический чек-лист: когда требовать цитат, как провоцировать «не знаю», что перепроверять у человека. Возвращается в Фазе 11 (фактчекинг) и в любых рабочих пайплайнах.

## Материалы

- [Anthropic — Reduce hallucinations](https://docs.claude.com/en/docs/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) — приёмы: право на «не знаю», цитаты, низкая температура.
- [anthropics/courses — Avoiding Hallucinations](https://github.com/anthropics/courses/blob/master/prompt_engineering_interactive_tutorial/Anthropic%201P/08_Avoiding_Hallucinations.ipynb) — интерактивный разбор на примерах.
- [Ji et al., 2022 — Survey of Hallucination in NLG](https://arxiv.org/abs/2202.03629) — обзор: типы галлюцинаций (intrinsic/extrinsic) и причины.

---
**Часы:** ~3 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
