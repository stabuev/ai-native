# Урок 11.1 · Конфиденциальность и корпоративные данные

**Фаза 11 — Этика, безопасность, governance** · **Результат фазы:** Оценить риски, настроить приватность и написать политику использования ИИ.
<!-- exercise -->

**Это вход в Фазу 11 — ответственность.** Мы научились строить, считать и выкатывать ИИ. Теперь — про то, что строить ИИ, который не навредит, не опция. И первый риск, с которым сталкивается любая команда, — утечка данных.

> **MOTTO.** Прежде чем отдать текст модели — пойми, что в нём: PII, секреты, тайну отдавать нельзя.

## PROBLEM

Самый частый ИИ-инцидент в компании прозаичен: сотрудник вставил в чат клиентские PII, API-ключ или коммерческую тайну, чтобы «модель помогла». Раз отправил во внешнюю модель — **контроль потерян**: текст ушёл на чужие серверы, мог осесть в логах, ретеншене, а в неудачном случае — в обучении.

Полагаться на бдительность сотрудника нельзя. Нужен **автоматический привратник** перед отправкой: найти и замаскировать PII, классифицировать чувствительность текста и решить, можно ли вообще слать его в данный канал. Соберём такой классификатор.

## CONCEPT

### Интуиция

Это **досмотр на выходе из здания**, а не доверие на слово. Каждый текст, уходящий наружу, проходит контроль: сканер ищет «запрещённое к выносу» (PII, секреты, карты), наклеивает на находки метку «замаскировано», а охрана по уровню секретности решает — выпустить через этот канал или нет. Публичную брошюру выносить можно; папку «совершенно секретно» — ни через какой внешний канал.

Ключевое правило: **чем чувствительнее данные, тем строже канал**. Не «удобно ли отправить», а «разрешено ли».

### Как это работает

```
текст → detect_pii (email / phone / card / secret)
            │
   classify_sensitivity: public < internal < confidential < restricted
            │
   redact (маскировка)  +  can_send(level, порог) → да/нет
```

- `detect_pii(text)` — найти сущности по regex: email, телефон, номер карты, секрет (ключи `sk-…`, `AKIA…`).
- `classify_sensitivity(text)` — уровень по находкам: секрет/карта → `restricted`; email/телефон → `confidential`; маркеры «для служебного» → `internal`; иначе `public`.
- `redact(text)` — заменить находки плейсхолдерами (`[EMAIL]`, `[SECRET]`).
- `can_send(level, max_allowed)` — сравнить уровень с порогом канала: выше порога → нельзя.

Порядок уровней — это упорядоченная шкала (`public < internal < confidential < restricted`), и решение об отправке — простое сравнение индексов. Так «можно ли слать» становится детерминированным правилом, а не решением уставшего человека.

## РАЗБОР ПО ШАГАМ

Прогоним привратник на тексте `"Клиент Иван, почта ivan@mail.ru, тел +7 999 123 45 67, ключ sk-secret123token"`:

```
1. detect_pii → [email: ivan@mail.ru, phone: +7 999 123 45 67, secret: sk-secret123token]
2. classify_sensitivity → есть secret → "restricted"  (максимальный уровень)
3. redact → "Клиент Иван, почта [EMAIL], тел [PHONE], ключ [SECRET]"
4. can_send("restricted", порог "internal"):
     ORDER.index("restricted")=3  >  ORDER.index("internal")=1  → False
```

Вывод: текст содержит секрет → уровень `restricted` → во внешнюю модель **не отправляется**. Обрати внимание на логику: **наивысшая** найденная сущность задаёт уровень всего текста (одного `sk-…`-ключа хватило, чтобы пометить весь фрагмент `restricted`), а решение `can_send` — это сравнение по шкале, а не «на глаз». Даже если бы текст всё же разрешили слать на пониженном уровне, в канал ушла бы **замаскированная** версия, без сырых PII. Поменяй regex на ML-детектор PII — контракт «найди → классифицируй → замаскируй → реши» не изменится.

## BUILD IT

**Задание: собери привратник конфиденциальности** — детектор PII, классификатор уровня, маскировку и решение об отправке. Только стандартная библиотека (`re`), без сети.

> **Перед запуском.** Работай в своей папке курса (`ai-native/11.1-privacy/`), а файлы урока клади в подпапку `code/` (по соглашению курса). Нужен только **Python 3** (для теста ещё `pytest`).

Создай файл `data_classifier.py`:

- regex-паттерны `PATTERNS` (`email`, `phone`, `card`, `secret`) и шкалу `ORDER = ["public","internal","confidential","restricted"]`.
- **`detect_pii(text)`** — список `{type, value}` по всем паттернам.
- **`classify_sensitivity(text)`** — `restricted`, если найдены `secret`/`card`; `confidential`, если `email`/`phone`; `internal`, если есть маркеры («внутрен», «конфиденциаль», «для служебного»); иначе `public`.
- **`redact(text)`** — заменить найденное на `[EMAIL]`/`[PHONE]`/`[CARD]`/`[SECRET]`.
- **`can_send(level, max_allowed="internal")`** — `ORDER.index(level) <= ORDER.index(max_allowed)`.

**Готово, когда** все тесты в `test_data_classifier.py` зелёные — они проверяют: детект email/phone/secret/card; уровни (секрет → restricted, почта → confidential, «для служебного» → internal, погода → public); `redact` убирает сырой PII и ставит `[EMAIL]`; `can_send` уважает порог (restricted → False).

```bash
pytest code -q              # красное → реализуй привратник → зелёное
python code/data_classifier.py # демо: текст с ключом → restricted, не отправляется
```

**Подсказка.** `classify_sensitivity` проверяет уровни **от высшего к низшему** (сначала secret/card, потом email/phone…) — высшая находка задаёт уровень. `redact` — `pat.sub(f"[{kind.upper()}]", text)` по каждому паттерну.

Внизу, в [«Исходниках урока»](#lesson-files), — три способа пройти упражнение (собрать самому · подсмотреть эталон · делегировать ИИ) и тесты-ТЗ.

## USE IT

Настройки приватности в инструментах (мульти-провайдер) — но сперва **знай, что куда уходит**:

- **Anthropic** — на данных бизнеса (Claude for Work / Enterprise / API) Anthropic **не обучает** модели по умолчанию; у consumer-продуктов (Free/Pro/Max) обучение — по **opt-in** (с включённым улучшением данные хранятся обезличенно до 5 лет, иначе чат удаляется в течение 30 дней). Для enterprise доступен **Zero Data Retention (ZDR)**. Сверяйся с актуальными privacy-условиями — они различаются для consumer и commercial.
- **OpenAI / Google** — enterprise-режимы с изоляцией данных и отключением обучения.
- **Data residency / суверенитет** — важно, **где физически лежат данные**. Пример (дословно из privacy policy DeepSeek): «we directly collect, process and store your Personal Data in People's Republic of China» — для регулируемых данных (GDPR и т.п.) это может быть стоп-фактором.
- **Open-weight как митигация** — DeepSeek / Llama / Qwen под открытой лицензией можно **запустить у себя** (self-host), и данные не покидают периметр. Решает приватность ценой инфраструктуры (не цены инференса).
- **Для своего пайплайна** — классификация + redaction **до** отправки (как в Build It); чувствительное — только в одобренные каналы или в self-host.

## SHIP IT

**Артефакт:** Политика обработки данных → [`outputs/data-policy.md`](../outputs/data-policy.md)

Политика: уровни данных, что в какие модели можно, обязательная redaction, retention. Дальше: фактчекинг и борьба с галлюцинациями (11.2), реестр рисков (11.3), общая политика ИИ (11.4), защита агентов (11.5).

## ЧАСТЫЕ ОШИБКИ

- **Полагаться на бдительность сотрудника.** Кто-нибудь вставит ключ или PII в чат. Нужен автоматический привратник (детект + redaction + правило отправки) до выхода данных наружу.
- **Маскировать, но не классифицировать (или наоборот).** Redaction убирает сырой PII, классификация решает, можно ли вообще слать. Нужны обе: замаскированный, но `restricted`-текст в публичный канал всё равно не должен уходить.
- **Игнорировать data residency.** «Не обучаются на данных» ≠ «данные в нужной юрисдикции». Где физически хранятся данные — отдельный вопрос (GDPR, госрегуляции); проверяй до интеграции.
- **Путать consumer и commercial условия.** У одного провайдера правила обучения/retention различаются для бесплатного чата и enterprise/API. Не переноси вывод с одного на другое — сверяйся с конкретными условиями.
- **Считать redaction идеальной.** Regex ловит типовые форматы, но пропустит нестандартный PII. Это первый барьер, не единственный; для чувствительного — одобренные каналы и self-host, а не только маскировка.

## ПРОВЕРЬ СЕБЯ

Ответь на вопросы — проверка сразу, с пояснением.

{{quiz}}

## Материалы

- [Anthropic — How long do you store my data](https://privacy.claude.com/en/articles/10023548-how-long-do-you-store-my-data) — retention и приватность.
- [Anthropic — Commercial Customers (privacy)](https://privacy.claude.com/en/collections/10663361-commercial-customers) — данные бизнеса не идут на обучение.
- [Anthropic — Updates to Consumer Terms](https://www.anthropic.com/news/updates-to-our-consumer-terms) — opt-in по использованию данных.
- [DeepSeek — Privacy Policy](https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html) — кейс data residency (хранение в КНР).
- [OpenAI — Enterprise privacy](https://openai.com/enterprise-privacy/) — не тренируют на business data по умолчанию, ZDR, EKM, BAA/HIPAA.
- [Google Workspace — Generative AI privacy & security](https://workspace.google.com/security/ai-privacy/) — данные Workspace не идут на обучение вне домена; ISO 42001, DLP, data-regions.
- [Microsoft Presidio](https://github.com/microsoft/presidio) — open-source детект и анонимизация PII (analyzer/anonymizer: replace/mask/redact) — ровно Build It урока.
- [OWASP — LLM02:2025 Sensitive Information Disclosure](https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/) — риск утечки PII/секретов через вывод; митигации (санитизация, least privilege). Кейс: утечка DeepSeek ClickHouse.
- [NIST — Privacy Framework](https://www.nist.gov/privacy-framework) — Identify-P / Govern-P / Control-P / Communicate-P / Protect-P; v1.1 покрывает AI-приватность.
- [TDS — PII anonymization with Microsoft Presidio (Medium)](https://medium.com/data-science/building-a-customized-pii-anonymizer-with-microsoft-presidio-b5c2ddfe523b) — практическая сборка кастомного анонимайзера.

---
**Часы:** ~3 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
