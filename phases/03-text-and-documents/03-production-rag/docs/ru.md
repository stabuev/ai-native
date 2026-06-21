# Урок 3.5 · Production RAG

**Фаза 3 — Текст и документы** · **Результат фазы:** Строить пайплайны резюмирования и редактуры; собрать базовый RAG над своим корпусом.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** Прод-RAG — это не «один ретривер», а гибрид сигналов, reranking и измеримое качество.

## PROBLEM

Базовый vector-RAG (3.3–3.4) в проде проседает: чистая семантика промахивается на точных терминах, кодах, именах; чистый keyword — на синонимах и перефразировках. А ещё непонятно, стало ли лучше. Прод-RAG объединяет **vector + keyword**, **переранжирует** результаты и **измеряет** качество ретрива и ответа.

## CONCEPT

```
запрос ─┬─ vector ranking (семантика, TF-IDF/эмбеддинги)
        └─ keyword ranking (точные слова)
                │ Reciprocal Rank Fusion (слияние рангов)
                ▼
        rerank → top-k → ответ
                │
        eval: faithfulness · context precision/recall (RAGAS)
```

Два рычага качества: **гибрид** (берём лучшее из двух ретриверов) и **оценка** (меряем заземлённость и релевантность, а не «на глаз»).

## BUILD IT

Гибридный ретривер (vector+keyword) + RRF-reranking, без зависимостей: [`code/hybrid_retriever.py`](../code/hybrid_retriever.py).

- `vector_ranking` / `keyword_ranking` — два независимых сигнала;
- `reciprocal_rank_fusion(rankings)` — слияние рангов (RRF);
- `hybrid_search(query, index, top_k)` — итоговый гибрид.

```bash
python code/hybrid_retriever.py
pytest code -q
```

Тест показывает суть: keyword ловит точный термин `numpy`, который чистый vector мог бы ранжировать ниже, а RRF сводит оба сигнала.

## USE IT

В проде — managed retrieval, графовый RAG и автоматическая оценка (мульти-провайдер):

- **GraphRAG** (Microsoft) — строит граф сущностей/связей и community-саммари: сильнее baseline-RAG на «глобальных» вопросах по большому корпусу.
- **Managed retrieval** — гибридный поиск из коробки (Chroma/pgvector/векторные БД), нейроэмбеддинги вместо TF-IDF.
- **RAGAS** — оценка пайплайна без ручной разметки: faithfulness, answer relevancy, context precision/recall — отдельно по ретриверу и генератору.

## SHIP IT

**Артефакт:** production-rag pipeline + eval-отчёт → [`outputs/production-rag-pipeline.md`](../outputs/production-rag-pipeline.md)

Рецепт прод-RAG (chunking → гибрид → rerank → ответ → eval) + шаблон отчёта по метрикам RAGAS. Связь с 3.2 (chunking), 3.3–3.4 (retrieval/store), 2.5/7.5 (eval).

## Материалы

- [Microsoft GraphRAG](https://microsoft.github.io/graphrag/) — графовый RAG для сложных запросов.
- [Ragas — метрики](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/) — faithfulness, context precision/recall.
- [Ragas (arXiv 2309.15217)](https://arxiv.org/abs/2309.15217) — first-source автоматической оценки RAG.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
