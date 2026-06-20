# Урок 3.4 · Векторные хранилища

**Фаза 3 — Текст и документы** · **Результат фазы:** Строить пайплайны резюмирования и редактуры; собрать базовый RAG над своим корпусом.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** Векторное хранилище — это память RAG: добавил документы → ищешь по смыслу.

## PROBLEM

В уроке 3.3 ретривер пересчитывал всё на каждый запрос и жил в памяти процесса. Для реального корпуса нужно **хранилище**: добавлять документы инкрементально, искать по близости и сохранять на диск, чтобы не индексировать заново. Это превращает retrieval в переиспользуемый ассистент по документам.

## CONCEPT

```
VectorStore:
  add(id, text)   → text → эмбеддинг → хранить (id, text, vec)
  query(text, k)  → эмбеддинг запроса → косинус → топ-k
  save/load       → персистентность на диск
```

Тот же интерфейс у Chroma/FAISS/pgvector — разница в масштабе и алгоритме поиска (точный перебор против ANN). Сначала собираем маленькое хранилище сами.

## BUILD IT

Мини векторное хранилище с персистентностью: [`code/vector_store.py`](../code/vector_store.py).

- `embed(text)` — **детерминированный** хеширующий эмбеддинг (встроенный `hash()` рандомизирован — нельзя);
- `VectorStore.add / query / save / load` — добавление, поиск по косинусу, сохранение/загрузка.

```bash
python code/vector_store.py
pytest code -q
```

Тест save/load доказывает персистентность: после загрузки с диска поиск даёт тот же результат — хранилище переживает перезапуск.

## USE IT

В проде подключаешь готовое хранилище и нейроэмбеддинги (мульти-провайдер):

```python
# Chroma (локально/сервер) — берёт эмбеддинги и индекс на себя
import chromadb
col = chromadb.PersistentClient(path="./db").get_or_create_collection("kb")
col.add(ids=ids, documents=docs)
col.query(query_texts=["вопрос"], n_results=5)

# FAISS — быстрый ANN-поиск по своим векторам (OpenAI/Google embeddings)
# pgvector — векторный поиск прямо в PostgreSQL
```

Тот же `add/query`, но индекс масштабируется на миллионы векторов (HNSW/IVF), а эмбеддинги считает нейросеть.

## SHIP IT

**Артефакт:** doc-assistant skill → [`outputs/doc-assistant/`](../outputs/doc-assistant/SKILL.md)

Скилл `doc-assistant`: складываешь корпус в хранилище и спрашиваешь его на естественном языке (retrieve → augment → ответ). Зарегистрирован в [`.claude/skills/doc-assistant`](../../../.claude/skills/doc-assistant/SKILL.md) — это итог Фазы 3 над собственным корпусом.

## Материалы

- [Chroma — Introduction](https://docs.trychroma.com/docs/overview/introduction) — открытое векторное хранилище для RAG.
- [facebookresearch/faiss](https://github.com/facebookresearch/faiss) — быстрый ANN-поиск по плотным векторам.
- [OpenAI — Embeddings guide](https://platform.openai.com/docs/guides/embeddings) — какие эмбеддинги класть в хранилище.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
