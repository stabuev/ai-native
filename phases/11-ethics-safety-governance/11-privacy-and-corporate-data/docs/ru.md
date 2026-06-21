# Урок 11.1 · Конфиденциальность и корпоративные данные

**Фаза 11 — Этика, безопасность, governance** · **Результат фазы:** Оценить риски, настроить приватность и написать политику использования ИИ.

> **MOTTO.** Прежде чем отдать текст модели — пойми, что в нём: PII, секреты, тайну отдавать нельзя.

## PROBLEM

Самый частый инцидент с ИИ в компании — утечка данных: сотрудник вставил в чат клиентские PII, ключи или коммерческую тайну. Раз отправил во внешнюю модель — контроль потерян. Нужен автоматический привратник: классифицировать чувствительность, найти и замаскировать PII, решить, можно ли отправлять.

## CONCEPT

```
текст → detect_pii (email/phone/card/secret)
            │
   classify_sensitivity: public < internal < confidential < restricted
            │
   redact (маскировка)  +  can_send(level, порог) → да/нет
```

Правило: чем чувствительнее данные, тем строже канал. Секреты/карты — `restricted`, во внешнюю модель не уходят; PII — маскируем; публичное — можно.

## BUILD IT

Классификатор чувствительности + детектор/маскировка PII: [`code/data_classifier.py`](../code/data_classifier.py).

- `detect_pii(text)` — email/phone/card/secret по regex;
- `classify_sensitivity(text)` — уровень public…restricted;
- `redact(text)` — маскировка; `can_send(level, max_allowed)` — решение об отправке.

```bash
python code/data_classifier.py
pytest code -q
```

Демо: текст с почтой, телефоном и ключом → `restricted`, маскируется, во внешнюю модель не отправляется.

## USE IT

Настройки приватности в инструментах (мульти-провайдер):

- **Anthropic** — commercial-данные (Claude for Work/Enterprise/API) **не идут на обучение**; consumer — по выбору; есть ZDR для enterprise, retention 30 дней для API.
- **OpenAI / Google** — enterprise-режимы с изоляцией данных и отключением обучения.
- **Data residency / суверенитет** — важно, *где* физически лежат данные. Пример: hosted DeepSeek API хранит данные в Китае (отсюда госбаны и GDPR-вопросы в ряде юрисдикций) — для регулируемых данных это стоп-фактор.
- **Open-weight как митигация** — DeepSeek/Llama/Qwen под открытой лицензией можно **запустить у себя** (self-host), и данные не покидают периметр. Решает приватность ценой инфраструктуры, не цены.
- Для своего пайплайна: классификация + redaction **до** отправки (как в Build It); чувствительное — только в одобренные каналы или в self-host.

## SHIP IT

**Артефакт:** Политика обработки данных → [`outputs/data-policy.md`](../outputs/data-policy.md)

Политика: уровни данных, что в какие модели можно, обязательная redaction, retention. Дальше: фактчекинг (11.2), реестр рисков (11.3), общая политика ИИ (11.4).

## Материалы

- [Anthropic — How long do you store my data](https://privacy.claude.com/en/articles/10023548-how-long-do-you-store-my-data) — retention и приватность.
- [Anthropic — Commercial Customers (privacy)](https://privacy.claude.com/en/collections/10663361-commercial-customers) — данные бизнеса не идут на обучение.
- [Anthropic — Updates to Consumer Terms](https://www.anthropic.com/news/updates-to-our-consumer-terms) — выбор по использованию данных.
- [DeepSeek — Privacy Policy](https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html) — кейс data residency (хранение в КНР) и зачем open-weight self-host.

---
**Часы:** ~3 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
