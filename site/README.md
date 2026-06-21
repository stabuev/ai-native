# site/ — статичный сайт курса AI Native

Лёгкий сайт без зависимостей и без фреймворков (plain HTML + vanilla JS + CSS), по образцу
[ai-engineering-from-scratch](https://github.com/stabuev/ai-engineering-from-scratch). Контент
генерируется из исходников курса — отдельная база не нужна.

## Сборка

```bash
node site/build.js
```

`build.js` читает `PROGRESS.md` (фазы, уроки, статус), `phases/*/*/docs/ru.md` (контент уроков,
рендерится Markdown → HTML) и `README.md` (часы и результат фазы), затем пишет **`site/data.js`**
(`META`, `PHASES`, `GLOSSARY`). Запускай после изменения уроков.

## Просмотр

```bash
# вариант 1 — открыть site/index.html напрямую в браузере (всё работает офлайн)
# вариант 2 — локальный сервер:
python3 -m http.server -d site 8000   # затем http://localhost:8000
```

## Файлы

| Файл | Назначение |
|---|---|
| `build.js` | генератор `data.js` из исходников курса (Node, без зависимостей) |
| `data.js` | сгенерированные данные (`META`, `PHASES`, `GLOSSARY`) — не редактировать вручную |
| `index.html` | главная: статистика, цикл, дорожная карта |
| `catalog.html` | каталог: 13 фаз / 59 уроков, статус, поиск, личный прогресс |
| `lesson.html` | просмотр урока (`lesson.html?id=1.1`), prev/next, отметка «пройдено» |
| `prereqs.html` | требования, формат Build/Use/Ship, карта моделей, оценивание |
| `glossary.html` | ключевые термины со ссылками на уроки |
| `style.css` | оформление (тёмная тема) |
| `header.js` / `app.js` / `progress.js` | навигация, рендеринг, прогресс (localStorage) |

## Деплой

Любой статик-хостинг (GitHub Pages / Netlify): публикуй папку `site/`. Перед публикацией
прогони `node site/build.js`, чтобы `data.js` соответствовал текущим урокам.
