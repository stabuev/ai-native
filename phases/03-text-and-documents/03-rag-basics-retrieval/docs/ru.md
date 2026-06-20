# Урок 3.3 · Основы RAG: retrieval

**Фаза 3 — Текст и документы** · **Результат фазы:** Строить пайплайны резюмирования и редактуры; собрать базовый RAG над своим корпусом.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** RAG — это «найди нужное, потом ответь»: retrieval решает, что модель вообще увидит.

## PROBLEM

Модель не знает твоих документов и выдумывает (урок 1.4), а весь корпус в окно не влезает (3.2). Решение — **RAG**: на запрос находим релевантные куски и подкладываем их в промпт. Сердце RAG — **retrieval**: как из тысяч кусков достать те самые. Сначала строим ретривер сами, чтобы понять механизм.

## CONCEPT

```
корпус → эмбеддинги (вектор на документ)
запрос → эмбеддинг запроса
            │ косинусная близость
            ▼
     топ-k ближайших кусков → в промпт модели
```

«Эмбеддинг» — это представление текста числами так, что похожее по смыслу близко в пространстве. В Build It роль эмбеддинга играет **TF-IDF**; в проде — нейроэмбеддинги, но принцип «вектор + близость» тот же.

## BUILD IT

TF-IDF ретривер с нуля: [`code/retriever.py`](../code/retriever.py).

- `build_index(docs)` — посчитать idf и tf-idf векторы документов;
- `search(query, index, k)` — топ-k по косинусной близости.

```bash
python code/retriever.py
pytest code -q
```

Тесты показывают суть retrieval: на «язык программирования» первым идёт док про Python, на «домашние животные» — про кошек/собак, а нерелевантный запрос даёт score 0.

## USE IT

Тот же retrieval — через нейроэмбеддинги и готовое хранилище (мульти-провайдер):

```python
# Эмбеддинги: OpenAI text-embedding-3-* / Google text-embedding / Voyage (для Anthropic)
emb = OpenAI().embeddings.create(model="text-embedding-3-small", input=docs)
# Хранилище: Chroma берёт индексацию и поиск на себя
import chromadb
col = chromadb.Client().create_collection("docs")
col.add(ids=ids, documents=docs)            # Chroma сам считает эмбеддинги
hits = col.query(query_texts=["мой вопрос"], n_results=3)
```

Принцип не изменился — поменялись только «эмбеддинг» (нейросеть вместо TF-IDF) и «индекс» (БД вместо словаря).

## SHIP IT

**Артефакт:** Мини-RAG скрипт → [`outputs/mini_rag.py`](../outputs/mini_rag.py)

Готовый `retrieve → augment → (generate)`: находит топ-k кусков и собирает промпт с контекстом. Полноценное хранилище — урок 3.4; первоисточник идеи — [RAG, Lewis et al. 2020](https://arxiv.org/abs/2005.11401).

## Материалы

- [Lewis et al., 2020 — Retrieval-Augmented Generation](https://arxiv.org/abs/2005.11401) — первоисточник RAG.
- [OpenAI — Embeddings guide](https://platform.openai.com/docs/guides/embeddings) — нейроэмбеддинги и косинусная близость.
- [Chroma — Introduction](https://docs.trychroma.com/docs/overview/introduction) — готовое хранилище для retrieval.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
