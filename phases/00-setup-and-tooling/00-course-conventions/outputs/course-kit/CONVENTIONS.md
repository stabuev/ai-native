# Соглашения курса (course-kit)

Контракт структуры и Definition of Done для курса в формате **Build It / Use It / Ship It**.
Используй вместе с `conventions.py` (scaffolder + валидатор) из этой же папки.

## Структура урока

```
phases/<NN>-<phase-slug>/<NN>-<lesson-slug>/
├── code/      Build It (с нуля, без фреймворков) + Use It + тест test_*.py
├── docs/ru.md разбор по 6 шагам
└── outputs/   артефакт: prompt · skill · agent · MCP
```

## 6 шагов в docs/ru.md

1. **MOTTO** — идея урока в одну строку.
2. **PROBLEM** — конкретная боль.
3. **CONCEPT** — интуиция и диаграммы (ASCII/mermaid).
4. **BUILD IT** — реализация с нуля в `code/`, запускается на CPU офлайн. Не догма: концептуальные/обзорные уроки бывают без `code/`. Где код содержательный — оформляй BUILD IT как **упражнение**: спека + тесты как ТЗ, эталон под катом, и три пути пройти его (собрать самому · подсмотреть эталон · делегировать ИИ).
5. **USE IT** — то же через реальный инструмент/API (платный ключ → пометка `**Requires:**`).
6. **SHIP IT** — артефакт в `outputs/` + как переиспользовать.

## Definition of Done

- `docs/ru.md` со всеми секциями (`MOTTO·PROBLEM·CONCEPT·BUILD IT·USE IT·SHIP IT`).
- В `outputs/` обещанный артефакт (непустой).
- **Если урок предполагает Build It-код:** рабочий код и, где осмысленно, проходящий `test_*.py`; `pytest <lesson>/code` зелёный. Код/тест только там, где они реально что-то объясняют.
- Код без платных ключей (исключения помечены `**Requires:**`).

## Автоматизация

```bash
python conventions.py                 # демо: scaffold + validate во временной папке
python -c "from conventions import validate_lesson as v; print(v('phases/01-how-llms-work/01-tokens-and-tokenization'))"
```

`validate_lesson(path)` возвращает список нарушений (пустой = готов). Повесь его в CI,
чтобы незаконченные уроки не проходили проверку.
