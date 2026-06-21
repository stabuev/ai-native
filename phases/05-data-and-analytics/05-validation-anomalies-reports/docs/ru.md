# Урок 5.5 · Валидация, аномалии, автоотчёты

**Фаза 5 — Данные и аналитика** · **Результат фазы:** Анализировать данные с ИИ, делать NL→SQL и автоотчёты с валидацией результатов.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** Цифру от ИИ нельзя показывать непроверенной: сначала валидация и поиск аномалий, потом отчёт.

## PROBLEM

ИИ-аналитик уверенно выдаёт числа — но мог взять не ту метрику, потерять строки или не заметить выброс. Если такой результат уйдёт в отчёт, цена ошибки высокая. Нужен **контроль качества**: проверки на вменяемость, детекция аномалий и сборка отчёта — автоматически, перед показом.

## CONCEPT

```
результат анализа
   │ validate_result (правила: неотрицательно, суммы сходятся, нет пропусков)
   │ find_anomalies  (z-score: что выбивается из ряда)
   ▼
build_report → отчёт с метриками и флагами → (по расписанию)
```

Это «фактчекинг для данных» (мост к Фазе 11). Автоотчёт = валидация + аномалии + сборка, запускаемые регулярно.

## BUILD IT

Валидация + детекция аномалий + сборка отчёта: [`code/validation.py`](../code/validation.py).

- `validate_result(metrics, rules)` — проверка по правилам-предикатам;
- `find_anomalies(series, z)` — выбросы по z-score (stdlib statistics);
- `build_report(title, metrics, anomalies)` — markdown-отчёт.

```bash
python code/validation.py
pytest code -q
```

Демо ловит выброс 500 в ряду (z=2.23) и собирает отчёт. Правила валидации — твои бизнес-инварианты (выручка ≥ 0, заказы > 0 и т.п.).

## USE IT

Автоотчёт по расписанию (мульти-провайдер): пайплайн «данные → анализ → валидация → аномалии → отчёт», запускаемый по cron / в оркестраторе, с уведомлением при флагах.

```python
metrics = run_daily_analysis()                 # NL→SQL (5.3) / агент (5.4)
problems = validate_result(metrics, RULES)
anomalies = find_anomalies(series)
report = build_report("Дневной отчёт", metrics, anomalies)
if problems or anomalies:
    notify(report)                             # алерт вместо «тихого» отчёта
```

В проде источник данных подключают через **MCP-коннектор к БД** (Фаза 6), а расписание — через планировщик (Genie/dbt jobs/cron).

## SHIP IT

**Артефакт:** Аналитический агент + (спека) MCP-коннектора к БД → [`outputs/analytics_agent.py`](../outputs/analytics_agent.py)

Готовый агент: SQL-выгрузка (sqlite) → валидация → аномалии → отчёт, плюс заметка о подключении БД через MCP (соберём в Фазе 6). Это итог фазы: сквозной пайплайн данные → анализ → проверка → отчёт.

## Материалы

- [scikit-learn — Outlier detection](https://scikit-learn.org/stable/modules/outlier_detection.html) — методы детекции аномалий за пределами z-score.
- [Anthropic — Reduce hallucinations](https://docs.claude.com/en/docs/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) — проверяемость и «не доверяй вслепую».
- [Databricks — AI/BI Genie](https://docs.databricks.com/aws/en/genie/) — автоматизация и MCP-доступ к данным.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
