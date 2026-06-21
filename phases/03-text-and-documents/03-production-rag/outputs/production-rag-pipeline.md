# Артефакт: production-RAG pipeline + eval-отчёт

Рецепт прод-RAG и шаблон отчёта по качеству. Код гибрида — [`code/hybrid_retriever.py`](../code/hybrid_retriever.py).

## Пайплайн

```
документы → chunking (overlap, урок 3.2)
          → индексация (vector + keyword)
запрос    → vector ranking ─┐
          → keyword ranking ─┤ RRF (слияние рангов)
                             → rerank → top-k
          → augment (контекст в промпт, требовать цитаты) → ответ
          → eval (RAGAS): faithfulness, context precision/recall
```

## Использование (код)

```python
from hybrid_retriever import build_index, hybrid_search
index = build_index(chunks)
hits = hybrid_search("вопрос пользователя", index, top_k=5)
# контекст = [h["doc"] for h in hits] → в промпт модели (mini_rag из 3.3)
```

## Шаблон eval-отчёта (RAGAS)

| Метрика | Что меряет | Значение | Порог |
|---|---|---|---|
| Faithfulness | ответ заземлён в контексте | 0.xx | ≥ 0.9 |
| Answer relevancy | ответ по вопросу | 0.xx | ≥ 0.85 |
| Context precision | релевантные чанки вверху | 0.xx | ≥ 0.8 |
| Context recall | нужное попало в контекст | 0.xx | ≥ 0.8 |

## Правила

- **Гибрид > один сигнал**: vector ловит смысл, keyword — точные термины; RRF сводит.
- **Меряй ретривер и генератор отдельно** (RAGAS) — так видно, где ломается.
- **Чанкинг с overlap** (3.2) и подсчёт бюджета (1.1) — основа.
- На «глобальных» вопросах по большому корпусу — рассмотри **GraphRAG**.
- Качество — в CI (порог на метрики), как evals (7.5).
