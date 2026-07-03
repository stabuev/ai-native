# Урок 6.3 · Свой MCP-сервер на FastMCP

**Фаза 6 — Инструменты и протоколы (MCP)** · **Результат фазы:** Объяснить tool use изнутри и поднять собственный MCP-сервер с контролем доступа.
<!-- exercise -->

**Requires (только для USE IT):** пакет `mcp` (FastMCP). BUILD IT работает офлайн, без зависимостей и без сети.

**В 6.2 мы поняли роли (host/client/server) без транспорта. Теперь — сам провод.** FastMCP поднимает сервер парой декораторов, но за этим «волшебством» стоит конкретный протокол. Увидим его под капотом — соберём сервер руками, потом запустим то же на SDK.

> **MOTTO.** MCP-сервер — это обработчик JSON-RPC: `initialize`, `tools/list`, `tools/call`.

## PROBLEM

`@mcp.tool()` — и инструмент готов. Удобно, но пока ты не знаешь, **какие сообщения** при этом летают, ты не сможешь ни отладить сервер, ни понять ошибку в логах, ни написать клиент.

Под капотом MCP — это **JSON-RPC 2.0**: клиент шлёт запрос с `method` и `params`, сервер отвечает либо `result`, либо `error` с кодом. Весь диалог сводится к трём методам: `initialize` (рукопожатие), `tools/list` (что есть), `tools/call` (выполнить). Соберём минимальный сервер, который правильно отвечает на эти запросы, — и FastMCP перестанет быть магией.

## CONCEPT

### Интуиция

JSON-RPC — это **строгий бланк заказа**. Клиент заполняет поля: «версия протокола `2.0`, номер заказа `id`, что делаем `method`, с чем `params`». Сервер обязан вернуть бланк-ответ с тем же `id` и либо `result` (готово), либо `error` с понятным **кодом** (что не так). Никакой свободной формы — поэтому любой клиент понимает любой сервер.

FastMCP заполняет эти бланки за тебя и строит схемы инструментов из подсказок типов и docstring. Но бланки — те же, что мы напишем вручную.

### Как это работает

```
client → {"jsonrpc":"2.0","id":1,"method":"initialize"}            → result: serverInfo, capabilities
client → {"method":"tools/list"}                                   → result: [{name, inputSchema}]
client → {"method":"tools/call","params":{name, arguments}}        → result: {content:[...]} | error
```

Три метода — три фазы жизни сервера:

- **`initialize`** — рукопожатие: сервер представляется (`serverInfo`) и сообщает возможности (`capabilities`).
- **`tools/list`** — discovery из 6.2: вернуть список инструментов с их `inputSchema`.
- **`tools/call`** — invoke: исполнить инструмент по `name` с `arguments`, вернуть `result.content`.

И стандартные коды ошибок JSON-RPC, которые сервер обязан отдавать вместо падения:

```
-32601  метод не найден      (нет такого method)
-32602  неверные параметры   (напр. неизвестный инструмент)
-32603  внутренняя ошибка    (инструмент упал при исполнении)
```

Транспорт (как байты доедут) — отдельный слой: **STDIO** локально, **Streamable HTTP** удалённо (6.4). Логика `handle` от транспорта не зависит.

## РАЗБОР ПО ШАГАМ

Прогоним `handle` на четырёх запросах к демо-серверу (инструменты `echo`, `add`):

```
1. {id:1, method:"initialize"}
   → result: {protocolVersion, capabilities:{tools:{}}, serverInfo:{name:"demo-server"}}

2. {id:2, method:"tools/list"}
   → result: {tools:[ {name:"echo", inputSchema:{...}}, {name:"add", inputSchema:{...}} ]}

3. {id:3, method:"tools/call", params:{name:"add", arguments:{a:2, b:3}}}
   → add(2,3)=5 → result: {content:[{type:"text", text:"5"}]}

4. {id:4, method:"no/such"}
   → error: {code:-32601, message:"method not found"}
```

Видно контракт: на каждый запрос — ответ с тем же `id`, в `result` или `error`. Результат `tools/call` оборачивается в `content` (список блоков), а число становится строкой `"5"` — MCP передаёт **контент**, не сырые типы. Неизвестный инструмент дал бы `-32602`, а упавший инструмент — `-32603`: сервер не падает, а возвращает ошибку по протоколу. Это ровно те сообщения, что генерирует FastMCP.

## BUILD IT

**Задание: собери мини MCP-сервер на JSON-RPC** — обработчик `initialize`/`tools/list`/`tools/call` с корректными ошибками. Только стандартная библиотека, без сети.

> **Перед запуском.** Работай в своей папке курса (`ai-native/6.3-mcp-server/`), а файлы урока клади в подпапку `code/` (как в 0.1). Нужен только **Python 3** (для теста ещё `pytest`).

Создай файл `mini_mcp_server.py`: dataclass `Tool(name, description, input_schema, fn)` и класс `MiniMCP(name, version)`:

- **`tool(name, description, input_schema)`** — декоратор, регистрирующий функцию как инструмент.
- хелперы ответа: `_ok(rid, result)` → `{"jsonrpc":"2.0","id":rid,"result":result}`; `_err(rid, code, message)` → аналогично с `error`.
- **`handle(request)`** — по `request["method"]`:
  - `initialize` → `result` с `protocolVersion`, `capabilities: {"tools": {}}`, `serverInfo: {name, version}`;
  - `tools/list` → `result` со списком `{name, description, inputSchema}`;
  - `tools/call` → найти инструмент по `params.name` (нет → `-32602`); исполнить `fn(**arguments)` (исключение → `-32603`); успех → `result` c `content: [{"type":"text","text": str(result)}]`;
  - иначе → `-32601`.

**Готово, когда** все тесты в `test_mini_mcp_server.py` зелёные — они проверяют: `initialize` отдаёт `serverInfo`; `tools/list` включает схемы; `tools/call add` даёт `"5"`; неизвестный инструмент → `-32602`; неизвестный метод → `-32601`.

```bash
pytest code -q              # красное → реализуй handle → зелёное
python code/mini_mcp_server.py # демо: initialize, tools/list, tools/call add(2,3)
```

**Подсказка.** Всегда возвращай тот же `id`, что пришёл. Оборачивай результат инструмента в `content` (список блоков). `tools/call` исполняй в `try/except`, отдавая `-32603` вместо проброса исключения — сервер не должен падать.

Внизу, в [«Исходниках урока»](#lesson-files), — три способа пройти упражнение (собрать самому · подсмотреть эталон · делегировать ИИ) и тесты-ТЗ.

## USE IT

То же самое — на **FastMCP** (официальный SDK `mcp`), транспорты STDIO и Streamable HTTP:

```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("Demo")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Сложить два числа"""
    return a + b

if __name__ == "__main__":
    mcp.run(transport="streamable-http")   # или STDIO по умолчанию
```

FastMCP сам строит `inputSchema` из аннотаций типов (`a: int`, `b: int`) и описание из docstring, и обрабатывает весь JSON-RPC — то есть делает ровно то, что мы написали в `handle` руками. Твоя работа сводится к функции с типами и докстрингом.

## SHIP IT

**Артефакт:** Рабочий MCP-сервер → [`outputs/mini_mcp_server.py`](../outputs/mini_mcp_server.py)

Минимальный сервер (`echo` + `add`) с корректным JSON-RPC — основа, к которой добавим тестирование и подключение к Claude Desktop / Cursor (6.4) и контроль доступа (6.5).

## ЧАСТЫЕ ОШИБКИ

- **Бросать исключение вместо JSON-RPC error.** Если инструмент упал, сервер обязан вернуть `error` с кодом (`-32603`), а не уронить соединение. Клиент ждёт бланк-ответ, а не стектрейс.
- **Путать коды ошибок.** `-32601` — нет метода, `-32602` — кривые параметры (напр. неизвестный инструмент), `-32603` — упал при исполнении. Неверный код путает клиент.
- **Терять `id` запроса.** Ответ должен нести тот же `id`, что и запрос, — иначе клиент не сопоставит ответ с вызовом.
- **Возвращать сырой результат вместо `content`.** `tools/call` отдаёт `result.content` (список блоков), а не голое число. MCP передаёт контент, а не питоновские типы.
- **Смешивать логику и транспорт.** `handle` обрабатывает сообщения и не должен знать про STDIO/HTTP. Транспорт — отдельный слой (6.4), иначе сервер не переносится.

## ПРОВЕРЬ СЕБЯ

Ответь на вопросы — проверка сразу, с пояснением.

{{quiz}}

## Материалы

- [MCP — Build an MCP server](https://modelcontextprotocol.io/docs/develop/build-server) — пошаговый гайд.
- [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) — официальный SDK с FastMCP.
- [FastMCP](https://gofastmcp.com) — расширенный фреймворк поверх SDK.
- [MCP — Server concepts](https://modelcontextprotocol.io/docs/learn/server-concepts) — как сервер отдаёт tools/resources/prompts и кто чем управляет (model/app/user).
- [MCP — Transports (спека 2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) — STDIO и Streamable HTTP: ровно транспорты из урока.
- [FastMCP — Create an MCP Server in Python (офиц. туториал)](https://gofastmcp.com/tutorials/create-mcp-server) — пошагово: tool из функции, ресурсы, запуск.
- [freeCodeCamp — Build Your First MCP Server using FastMCP](https://www.freecodecamp.org/news/how-to-build-your-first-mcp-server-using-fastmcp/) — авторитетный практический разбор.
- [FastMCP: Build your First MCP Server (YouTube)](https://www.youtube.com/watch?v=UVf-hLVbdrQ) — видео-туториал по сборке сервера на FastMCP.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
