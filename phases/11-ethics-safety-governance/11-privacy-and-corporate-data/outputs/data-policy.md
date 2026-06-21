# Артефакт: политика обработки данных для ИИ

Что и в какие модели можно отдавать. Привратник в коде — [`code/data_classifier.py`](../code/data_classifier.py).

## Уровни данных и каналы

| Уровень | Примеры | Куда можно |
|---|---|---|
| public | маркетинг, открытые доки | любые модели |
| internal | внутренние заметки, процессы | enterprise/no-train режим |
| confidential | PII (email/phone), переписка клиентов | только одобренный enterprise-канал, с redaction |
| restricted | секреты, ключи, карты, тайна | НЕ отправлять во внешнюю модель |

## Обязательные правила

- [ ] **Redaction до отправки** — маскируй PII/секреты (`redact`) перед вызовом модели.
- [ ] **Классифицируй вход** — `classify_sensitivity` + `can_send` как привратник в пайплайне.
- [ ] **Enterprise-режим** — бизнес-данные только туда, где **нет обучения на них** (commercial terms / ZDR).
- [ ] **Retention** — знай срок хранения у провайдера; для чувствительного — ZDR/30 дней.
- [ ] **Без секретов в промптах** — ключи только из окружения (урок 0.2), не в тексте.
- [ ] **Data residency** — знай юрисдикцию хранения (напр. hosted DeepSeek API → КНР, бан для регулируемых данных); сверяйся с GDPR/локальными требованиями.
- [ ] **Open-weight self-host** — для самых чувствительных данных запускай open-weight модель (DeepSeek/Llama/Qwen) у себя: данные не покидают периметр.

## Применение (код)

```python
from data_classifier import classify_sensitivity, redact, can_send
level = classify_sensitivity(text)
if not can_send(level, max_allowed="confidential"):
    raise PermissionError(f"{level}: нельзя во внешнюю модель")
payload = redact(text)
```

## Связи

- Ключи и окружение → урок 0.2 · Что нельзя отдавать модели → урок 6.5
- Политика ИИ целиком → урок 11.4 · GDPR/EU AI Act → уроки 11.3–11.4
