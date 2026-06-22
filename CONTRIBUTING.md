# Как вносить вклад в AI Native

Спасибо за интерес! Курс строится по единому каркасу **Build It / Use It / Ship It**.
Перед добавлением урока загляни в [`CLAUDE.md`](CLAUDE.md) (правила формата) и [`LESSON_TEMPLATE.md`](LESSON_TEMPLATE.md) (шаблон).

## Структура урока

```
phases/<NN>-<phase-slug>/<NN>-<lesson-slug>/
├── code/        Build It (с нуля, без фреймворков) + тест test_*.py
├── docs/ru.md   разбор по 6 шагам: MOTTO · PROBLEM · CONCEPT · BUILD IT · USE IT · SHIP IT
└── outputs/     артефакт: prompt · skill · agent · MCP
```

Слаги фаз и уроков зафиксированы в `README.md` (колонка «Папка») — не переименовывай.

## Definition of Done

- [ ] `docs/ru.md` заполнен по всем 6 шагам + блок `## Материалы` (2–4 **проверенные** ссылки).
- [ ] В `code/` рабочая реализация и проходящий `test_*.py` (офлайн, на CPU, без платных ключей; исключение помечается `**Requires:**`).
- [ ] В `outputs/` лежит обещанный артефакт (см. колонку Ship It в README).
- [ ] `pytest phases/<...>/code` зелёный; общий `pytest -q` не сломан.
- [ ] Отмечен `[x]` в `PROGRESS.md`.

Проверить структуру автоматически:

```bash
python -c "import sys; sys.path.insert(0,'phases/00-setup-and-tooling/00-course-conventions/code'); \
from conventions import validate_lesson; print(validate_lesson('phases/<...>') or 'OK')"
```

## Стиль

- Объяснения по-русски, код и идентификаторы — по-английски.
- Минимум зависимостей; стандартная библиотека по умолчанию.
- Никаких заглушек — только рабочие примеры.
- Use It — мульти-провайдер (Claude / OpenAI / Gemini, где уместно — open-weight).
- Ссылки в «Материалах» **проверяй** (не выдумывай URL).
- Образец: `phases/01-how-llms-work/01-tokens-and-tokenization/`.

## Перед коммитом

```bash
pip install -r requirements.txt
pytest -q                 # все тесты зелёные
node site/build.js        # пересобрать сайт (data.js), если менял уроки
```

Коммит — один на завершённую фазу (`Phase <N> (<slug>): lessons complete`); пуш — за мейнтейнером.

## Прочее

- Новые термины — в [`glossary/terms.md`](glossary/terms.md).
- Баги и предложения — через Issues. Спасибо за вклад! ❤️
