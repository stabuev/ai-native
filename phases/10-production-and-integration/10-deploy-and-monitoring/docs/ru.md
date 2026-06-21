# Урок 10.2 · Деплой и мониторинг

**Фаза 10 — Production и интеграция** · **Результат фазы:** Встроить ИИ в рабочий инструмент с мониторингом токенов и стоимости.
<!-- **Requires:** прод-окружение / observability-бэкенд — только для блока USE IT -->

> **MOTTO.** Задеплоил — значит измеряешь: без логов prompt/response и метрик здоровья прод вслепую.

## PROBLEM

После выкладки ИИ-процесса нужно знать: не растёт ли доля ошибок, не деградирует ли латентность, что именно сломалось. Без структурного логирования вызовов и метрик мониторинга «у пользователя не работает» превращается в гадание. ИИ ещё и недетерминирован — наблюдаемость критична вдвойне.

## CONCEPT

```
каждый вызов → лог {model, latency, status, error}
                     │
   метрики:  error_rate · p50/p95 latency · recent_errors
                     │
              алерты при превышении порогов
```

Логируй то, что позволит отладить и оценить здоровье: модель, латентность, статус, ошибку (и при согласии — содержимое, с редактированием PII).

## BUILD IT

Структурный логгер вызовов + метрики: [`code/monitoring.py`](../code/monitoring.py).

- `CallLogger.log(model, latency_ms, ok, error)` — запись вызова;
- `error_rate()`, `latency_percentile(p)`, `recent_errors()` — метрики мониторинга.

```bash
python code/monitoring.py
pytest code -q
```

Демо: 1 ошибка из 5 → error_rate 0.2, p95 latency ловит «хвост» 1500ms. Это сырьё для алертов и дашборда.

## USE IT

Запуск процесса в проде с observability (мульти-провайдер):

- **OpenTelemetry GenAI** — стандарт семантических конвенций (`gen_ai.*`): модель, токены, латентность, tool-calls — единый формат для любого вендора.
- **Langfuse / аналоги** — трейсинг вызовов, ошибок и токенов; LLM-as-judge для качества.
- **Алерты** — на error_rate, p95 latency, всплеск стоимости; редактируй PII перед логированием контента.

## SHIP IT

**Артефакт:** Мониторинг-конфиг → [`outputs/monitoring-config.md`](../outputs/monitoring-config.md)

Конфиг: что логировать, какие метрики, пороги алертов, политика по PII. Дальше: телеметрия токенов/стоимости и воспроизводимость (10.3).

## Материалы

- [OpenTelemetry — GenAI observability](https://opentelemetry.io/blog/2026/genai-observability/) — трейсинг вызовов LLM.
- [OpenTelemetry — for Generative AI](https://opentelemetry.io/blog/2024/otel-generative-ai/) — семантические конвенции `gen_ai.*`.
- [Langfuse — Observability](https://langfuse.com/docs/observability/overview) — трейсинг, ошибки, токены, оценка.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
