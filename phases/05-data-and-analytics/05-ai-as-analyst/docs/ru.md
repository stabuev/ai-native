# Урок 5.1 · ИИ как аналитик

**Фаза 5 — Данные и аналитика** · **Результат фазы:** Анализировать данные с ИИ, делать NL→SQL и автоотчёты с валидацией результатов.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** Аналитика — это план: что сгруппировать, что посчитать, как агрегировать; ИИ строит план, код его исполняет.

## PROBLEM

«Посмотри данные и скажи, что интересного» — звучит как магия, пока не видишь механику. ИИ-аналитик не «понимает» таблицу мистически: он превращает вопрос в **план** (группировка + метрика + агрегация) и исполняет его кодом. Поймём этот механизм, собрав мини-аналитику на stdlib.

## CONCEPT

```
вопрос → план анализа → исполнение → результат
          group_by      aggregate     числа/топ
          metric        (sum/mean/count)
```

Это split-apply-combine: сгруппировать строки, применить агрегат, собрать ответ. Ровно это делает pandas (и ChatGPT/Claude под капотом) — мы делаем то же руками.

## BUILD IT

Мини-аналитика на stdlib (csv, statistics): [`code/analyze.py`](../code/analyze.py).

- `load_csv(text)` — таблица как список словарей;
- `aggregate(rows, group_by, value, agg)` — sum/mean/count по группам;
- `top_n(d, n)` — топ по значению.

```bash
python code/analyze.py
pytest code -q
```

План задаётся параметрами — это и есть «промпт → план → исполнение», только без LLM, чтобы видеть суть.

## USE IT

Тот же анализ — через pandas и загрузку файла в чат (мульти-провайдер):

```python
import pandas as pd
df = pd.read_csv("sales.csv")
df.groupby("region")["amount"].sum().sort_values(ascending=False)   # то же, что aggregate+top_n
```

- **ChatGPT** — загрузи CSV/Excel, спроси «выручка по регионам, топ-5» → выполнит pandas-код и построит график.
- **Claude** — загрузка файла в чат/Project, тот же запрос; через API — code execution tool.

⚠️ ИИ не знает происхождения данных и допущений — результат **проверяй** (урок 5.5).

## SHIP IT

**Артефакт:** Шаблон аналитического запроса → [`outputs/analysis-request-template.md`](../outputs/analysis-request-template.md)

Структура запроса к ИИ-аналитику (данные · вопрос · метрика · разрез · формат · проверка) — чтобы ответы были воспроизводимы и проверяемы. Дальше: исполнение кода (5.2), NL→SQL (5.3).

## Материалы

- [pandas — Getting started](https://pandas.pydata.org/docs/getting_started/index.html) — стандартный инструмент анализа данных.
- [OpenAI — Data analysis with ChatGPT](https://help.openai.com/en/articles/8437071-code-interpreter) — анализ загруженных файлов.
- [Anthropic — Code execution tool](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/code-execution-tool) — анализ данных кодом через API.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
