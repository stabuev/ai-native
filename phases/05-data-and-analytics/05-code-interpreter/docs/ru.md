# Урок 5.2 · Code Interpreter

**Фаза 5 — Данные и аналитика** · **Результат фазы:** Анализировать данные с ИИ, делать NL→SQL и автоотчёты с валидацией результатов.
<!-- **Requires:** платный API-ключ — только для блока USE IT -->

> **MOTTO.** Code Interpreter = модель пишет код, песочница его исполняет и возвращает результат.

## PROBLEM

LLM плохо считает «в уме» (арифметика, статистика), но отлично **пишет код**. Code Interpreter замыкает цикл: модель генерирует Python, изолированная среда его исполняет, результат и ошибки возвращаются модели. Чтобы это не было магией — соберём упрощённую песочницу и поймём, где границы безопасности.

## CONCEPT

```
запрос → модель пишет код → [ sandbox: исполнить ] → результат/ошибка → модель
                                  │ ограниченные builtins
                                  │ нет сети, изоляция, лимиты
                                  ▼ self-correction по ошибке
```

Ключ — **изоляция**: код модели нельзя пускать в обычный процесс. Настоящий Code Interpreter крутится в контейнере без сети; наша версия — учебная, показывает идею и проверки.

## BUILD IT

Упрощённый sandbox-исполнитель: [`code/sandbox.py`](../code/sandbox.py).

- `unsafe_tokens(code)` — статическая проверка на запрещённое (`import`, `__`, `open(`, `os.`…);
- `run_code(code, data)` — исполнить в окружении с ограниченными builtins; результат — переменная `result`.

```bash
python code/sandbox.py
pytest code -q
```

⚠️ Честная оговорка: это **не настоящая изоляция** — ограниченные builtins и проверки лишь демонстрируют принцип. Для прода нужен контейнер/seccomp/отдельный процесс с лимитами (безопасность — урок 6.5).

## USE IT

Готовый Code Interpreter — расчёты и графики (мульти-провайдер):

- **ChatGPT** — Advanced Data Analysis: загрузка файла → «построй регрессию и график» → выполнит pandas/matplotlib в изолированной среде (без сети, инстанс уничтожается).
- **OpenAI API** — Code Interpreter tool в Responses/Assistants.
- **Claude** — `code_execution` server-tool: Python в песочнице Anthropic, в т.ч. над файлами из Files API.

Везде один паттерн: модель пишет код → песочница исполняет → результат назад, с авто-исправлением ошибок.

## SHIP IT

**Артефакт:** Набор аналитических промптов → [`outputs/analysis-prompts.md`](../outputs/analysis-prompts.md)

Промпты для Code Interpreter под типовые задачи (профилирование, агрегации, графики, проверка гипотез) с требованием показать код. Дальше: NL→SQL для запросов к БД (5.3).

## Материалы

- [OpenAI — Code Interpreter (API)](https://platform.openai.com/docs/guides/tools-code-interpreter) — инструмент исполнения кода.
- [OpenAI — Data analysis with ChatGPT](https://help.openai.com/en/articles/8437071-code-interpreter) — как устроена изоляция и работа с файлами.
- [Anthropic — Code execution tool](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/code-execution-tool) — Python в песочнице Claude.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
