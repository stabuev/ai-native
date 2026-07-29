# Артефакт: решение по retrieval-конфигурации и eval-отчёт

Заполненный decision record для учебного корпуса 3.3–3.5. Значения получены из
[`code/hybrid_retriever.py`](../code/hybrid_retriever.py) и
[`code/sample_rankings.py`](../code/sample_rankings.py), а не назначены как универсальные
пороги.

**Статус:** `hybrid, top_k=2` выбран кандидатом для следующего интеграционного прогона.
Это ещё не доказательство production-готовности.

## Проверяемое изменение

Baseline — два независимых способа получить положительных кандидатов:

```text
query ─┬─ lexical retriever ─► ranked record IDs ─┐
       └─ dense retriever   ─► ranked record IDs ─┤
                                                   ▼
                                      RRF, rank_constant=60
                                                   │
                                                   ▼
                                      top-k canonical records
                                      + id/source/positions
                                      + matched_by/ranks
                                                   │
                            ┌──────────────────────┴─────────────────────┐
                            ▼                                            ▼
                 insufficient_context                    optional pairwise reranker
                                                                      │
                                                                      ▼
                                                            grounded generation
```

RRF здесь является **rank fusion**, а не pairwise reranker. Если оба retriever вернули
пустые списки, fusion возвращает `[]` и генерация не запускается.

## Данные и критерий

- 4 traceable records из одного учебного документа;
- 6 eval cases: 5 ответимых и 1 запрос вне корпуса;
- один ожидаемый ID на каждый ответимый запрос;
- lexical, dense и hybrid сравниваются на одинаковых cases и одинаковом `top_k`;
- ответимый case проходит, если ожидаемый ID входит в top-k;
- no-answer case проходит только при пустой выдаче;
- ranking fixtures воспроизводят возможные успехи и ошибки, но не измеряют конкретную
  embedding-модель.

## Сводка

| Вариант | Passed при top-1 | Passed при top-2 | Ответимые Hit@2 | No-answer accuracy |
|---|---:|---:|---:|---:|
| lexical | 4/6 | 4/6 | 3/5 | 1/1 |
| dense | 4/6 | 5/6 | 4/5 | 1/1 |
| hybrid, RRF | **5/6** | **6/6** | **5/5** | **1/1** |

Увеличение `top_k` сравнивается отдельным прогоном. Нельзя приписывать разницу только
RRF: больший top-k сам по себе повышает шанс оставить ожидаемый ID и одновременно
увеличивает объём и возможный шум контекста.

## Per-case разбор при top-1

| Case | Ожидаемый ID | Lexical | Dense | Hybrid | Вывод |
|---|---|---:|---:|---:|---|
| `exact-launch` | `chunk-0000` | ✓ | ✗ | ✓ | Два сигнала вернули точный record на первое место |
| `owner-paraphrase` | `chunk-0005` | ✗ | ✓ | ✓ | Hybrid сохранил dense-only перефразировку |
| `safety-gate` | `chunk-0002` | ✓ | ✓ | ✓ | Сигналы согласны |
| `pilot-metrics` | `chunk-0004` | ✓ | ✗ | ✓ | Lexical исправил dense-промах |
| `outside-corpus` | `[]` | ✓ | ✓ | ✓ | Пустая выдача сохранилась |
| `support-role` | `chunk-0005` | ✗ | ✓ | ✗ | Tie двух одиночных списков выбрал первый lexical ID |

Aggregate hybrid лучше обоих top-1 baselines, но `support-role` показывает регрессию
относительно dense. Она не скрывается общей цифрой `5/6`.

## Почему выбран top-2

При `top_k=2` hybrid оставляет оба конфликтующих кандидата в `support-role` и проходит
все 6 учебных cases. Dense проходит 5/6, lexical — 4/6. Поэтому текущий кандидат:

```yaml
retrieval:
  signals: [lexical, dense]
  fusion: rrf
  rank_constant: 60
  top_k: 2
  on_no_evidence: insufficient_context
```

Решение ограничено retrieval-этапом. Перед реальным rollout нужно проверить, что второй
чанк не ухудшает генерацию, latency и стоимость. Если конфликтующие кандидаты часто
загрязняют контекст, следующий эксперимент — pairwise reranker над объединённым пулом,
а не скрытое изменение tie-break.

## Воспроизведение

```bash
pytest code -q
python code/hybrid_retriever.py
```

Программный доступ:

```python
from hybrid_retriever import evaluate, hybrid_search
from sample_rankings import EVAL_CASES, SAMPLE_RECORDS

top_one = evaluate(EVAL_CASES, SAMPLE_RECORDS, top_k=1)
top_two = evaluate(EVAL_CASES, SAMPLE_RECORDS, top_k=2)

rankings = EVAL_CASES[0]["rankings"]
evidence = hybrid_search(rankings, SAMPLE_RECORDS, top_k=2)
```

В `evidence` каждый hit содержит неизменённый canonical record и отдельный fusion trace:
`rrf_score`, `matched_by`, `ranks`.

## Перенос на свой корпус

1. Сохрани единый record contract: стабильные `id`, `source`, `text` и позиции.
2. Получи реальные positive candidate IDs от lexical и dense retriever.
3. Зафиксируй версии индексов и embedding model.
4. Собери answerable, no-answer, пограничные и критические eval cases.
5. Сравни lexical, dense и hybrid при одном `top_k`.
6. Просмотри per-case gains и regressions до aggregate.
7. Отдельно сравни `top_k`, latency, размер контекста и стоимость.
8. Зафиксируй принятое решение, известные провалы и условие rollback.

Шаблон строки для нового случая:

```yaml
id: stable-case-id
query: вопрос пользователя
expected_ids: [document.md#chunk-0012]
rankings:
  lexical: [document.md#chunk-0012]
  dense: [document.md#chunk-0007, document.md#chunk-0012]
critical: true
decision: pass | investigate | block
```

Поле `critical` и решение остаются частью человеческого decision record: учебная
`evaluate()` не превращает цену ошибки в одну среднюю цифру.

## Следующий слой: генерация

После принятия retrieval-конфигурации добавь eval ответа:

- faithfulness относительно найденного контекста;
- response relevancy относительно запроса;
- context precision/recall с явно указанными reference inputs;
- примеры неподдержанных утверждений, а не только средние scores.

Для LLM-based метрик зафиксируй evaluator model, prompt, версию библиотеки, число
повторов, стоимость и дату запуска. Порог принимается относительно baseline и цены
ошибки своего процесса, а не копируется из этого отчёта.

## Почему это ещё не production-ready

Учебный отчёт не проверяет:

- репрезентативность большого реального корпуса;
- качество конкретных lexical и dense моделей;
- обновление индексов и совместимость версий;
- права доступа к документам;
- latency, throughput и стоимость;
- monitoring, rollout и rollback;
- устойчивость генерации и безопасность.

Он доказывает более узкий, но необходимый результат: fusion работает воспроизводимо,
не создаёт evidence из пустоты, сохраняет provenance и сравнивается с baseline без
сокрытия регрессий.
