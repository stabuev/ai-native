# Урок 6.2 · Архитектура MCP

**Фаза 6 — Инструменты и протоколы (MCP)** · **Результат фазы:** Объяснить tool use изнутри и поднять собственный MCP-сервер с контролем доступа.
<!-- exercise -->

**Requires (только для USE IT):** клиент с поддержкой MCP (Claude Desktop / Claude Code / Cursor). BUILD IT работает офлайн, без ключей и без сети.

**В 6.1 инструменты были «вшиты» в приложение.** Это не масштабируется: у каждого приложения свои инструменты, переиспользовать их между Claude, Cursor и твоими агентами нельзя. MCP решает ровно эту проблему — стандартом подключения.

> **MOTTO.** MCP — это USB-C между ИИ и миром: один протокол, три примитива (tools/resources/prompts).

## PROBLEM

Ты написал инструмент «прочитать таблицу из БД». Чтобы дать его Claude Desktop — пишешь интеграцию под Claude. Для Cursor — переписываешь под Cursor. Для своего агента — снова с нуля. N инструментов × M приложений = хаос несовместимых интеграций.

Так же когда-то было с периферией: у каждого устройства свой разъём. Пришёл **USB-C** — один разъём для всего. **MCP (Model Context Protocol)** — это USB-C для ИИ: один протокол, по которому **любой** клиент находит и зовёт инструменты **любого** сервера. Написал MCP-сервер один раз — он работает в каждом MCP-совместимом приложении.

## CONCEPT

### Интуиция

Три роли, как в ресторане:

- **Host** — приложение с LLM (Claude Desktop, IDE, твой агент). Это **посетитель**, который хочет что-то получить.
- **Client** — коннектор внутри host, по одному на каждый сервер (1:1). Это **официант**: говорит на языке протокола, носит запросы туда-обратно.
- **Server** — отдаёт возможности. Это **кухня**: умеет готовить (tools), хранит продукты (resources) и держит рецепты (prompts).

Посетитель не лезет на кухню напрямую — общение идёт через официанта по стандартному протоколу (JSON-RPC 2.0). Поэтому любая кухня (сервер) работает с любым посетителем (host), у которого есть официант (client).

### Как это работает

```
   Host (приложение с LLM)
     └─ Client ⇄ Server     (1 client ↔ 1 server, JSON-RPC 2.0)
                   ├─ tools      действия (как POST: что-то делают)
                   ├─ resources  данные (как GET: читаются по URI)
                   └─ prompts    заготовки-шаблоны
        discovery (list) → invoke (call)
```

Три примитива сервера:

- **tools** — действия (посчитать, записать в БД, отправить письмо). Аналог POST — у них есть эффект; это и есть tool_call из 6.1.
- **resources** — данные, читаемые по URI (файл, запись, документ). Аналог GET — только отдают.
- **prompts** — готовые шаблоны-заготовки с подстановкой переменных.

И две фазы общения:

- **discovery** — клиент спрашивает «что ты умеешь?» (`list_tools` / `list_resources` / `list_prompts`). Так host узнаёт возможности, не зашивая их заранее.
- **invoke** — клиент вызывает конкретное (`call_tool` / `read_resource` / `get_prompt`).

Соберём это in-process, без транспорта, чтобы увидеть роли чисто; настоящий JSON-RPC-транспорт добавим в 6.3.

## РАЗБОР ПО ШАГАМ

Поднимем сервер с тремя примитивами и сходим в него клиентом:

```
srv.add_tool("sum", lambda a,b: a+b, "сложить")
srv.add_resource("doc://policy", "Возврат в течение 14 дней.")
srv.add_prompt("greet", "Привет, {name}!")
```

**1. discovery** — клиент спрашивает, что есть:

```
client.discover() → {
  tools:     [{name: "sum", description: "сложить"}],
  resources: ["doc://policy"],
  prompts:   ["greet"],
}
```

**2. invoke** — клиент вызывает каждый примитив:

```
client.call("sum", a=2, b=3)        → 5                          (tool: действие)
srv.read_resource("doc://policy")   → "Возврат в течение 14 дней." (resource: данные)
srv.get_prompt("greet", name="Иван") → "Привет, Иван!"            (prompt: шаблон)
```

Видно разделение ролей: сервер только публикует и исполняет примитивы, клиент только перечисляет и зовёт, host (в демо — функция `__main__`) оркеструет. Запрос несуществующего (`call_tool("nope")`) поднимает ошибку — сервер отвечает только за то, что объявил в discovery. Тот же сервер подключишь к Claude Desktop или Cursor — код сервера не изменится.

## BUILD IT

**Задание: собери in-process модель MCP** — сервер с тремя примитивами и клиент с discovery/invoke. Только стандартная библиотека, без сети.

> **Перед запуском.** Работай в своей папке курса (`ai-native/6.2-mcp-architecture/`), а файлы урока клади в подпапку `code/` (как в 0.1). Нужен только **Python 3** (для теста ещё `pytest`).

Создай файл `mcp_architecture.py` с двумя классами:

- **`MCPServer(name)`** — хранит три реестра. Методы регистрации: `add_tool(name, fn, description="")`, `add_resource(uri, content)`, `add_prompt(name, template)`. Discovery: `list_tools()` (список `{name, description}`), `list_resources()`, `list_prompts()`. Invoke: `call_tool(name, **args)` (исполнить `fn`, нет — `KeyError`), `read_resource(uri)`, `get_prompt(prompt_name, **variables)` (вернуть `template.format(**variables)`).
- **`MCPClient(server)`** — `discover()` возвращает `{"tools", "resources", "prompts"}`; `call(tool, **args)` проксирует в `server.call_tool`.

**Готово, когда** все тесты в `test_mcp_architecture.py` зелёные — они проверяют: discovery перечисляет все три примитива; `call("sum", a=2, b=3)` = 5; ресурс и промпт читаются (промпт подставляет имя); запрос неизвестного примитива → `KeyError`.

```bash
pytest code -q              # красное → реализуй сервер и клиент → зелёное
python code/mcp_architecture.py # демо: discovery + вызов tool/resource/prompt
```

**Подсказка.** Три словаря под примитивы. `call_tool` исполняет `self._tools[name]["fn"](**args)`. `get_prompt` — это `template.format(**variables)`. Перед invoke проверяй наличие ключа и кидай `KeyError` с понятным текстом.

Внизу, в [«Исходниках урока»](#lesson-files), — три способа пройти упражнение (собрать самому · подсмотреть эталон · делегировать ИИ) и тесты-ТЗ.

## USE IT

Готовых MCP-серверов уже десятки — подключаешь без единой строчки кода (мульти-платформа):

- **Claude Desktop / Claude Code** — добавить сервер в конфиг MCP; клиент сам сделает discovery и покажет инструменты.
- **Cursor и другие host'ы** — тот же протокол, свои настройки подключения.
- Реестр референс-серверов — `modelcontextprotocol/servers` (файлы, БД, GitHub, поиск и др.).

Смысл стандарта: один сервер работает в любом MCP-совместимом host. Написал — переиспользуешь везде, без N×M интеграций.

## SHIP IT

**Артефакт:** Карта MCP под свой стек → [`outputs/mcp-map.md`](../outputs/mcp-map.md)

Карта: какие данные и инструменты вынести в свои MCP-серверы, какие готовые коннекторы подключить, что к какому host'у. Это план перед тем, как поднять собственный сервер на FastMCP (6.3) и закрыть его доступом (6.5).

## ЧАСТЫЕ ОШИБКИ

- **Путать host, client и server.** Host — приложение с LLM, client — коннектор внутри него (1:1 к серверу), server — отдаёт примитивы. Сервер не «знает» про модель; он просто публикует возможности.
- **Путать tools и resources.** tools — действия с эффектом (как POST), resources — данные для чтения по URI (как GET). Запись в БД — это tool, чтение записи — resource.
- **Зашивать возможности в host вместо discovery.** Смысл MCP — клиент сам узнаёт, что умеет сервер (`list_*`). Хардкод списка инструментов ломает переносимость.
- **Думать, что MCP заменяет tool use.** Под капотом тот же цикл из 6.1 (схема → вызов → результат). MCP лишь стандартизирует, **как** это передаётся между процессами.
- **Игнорировать, что сервер — граница доверия.** Сервер исполняет вызовы и отдаёт данные; что именно он открывает модели — вопрос безопасности (6.5), а не только удобства.

## ПРОВЕРЬ СЕБЯ

Ответь на вопросы — проверка сразу, с пояснением.

{{quiz}}

## Материалы

- [MCP — Specification](https://modelcontextprotocol.io/specification/2025-11-25) — протокол, примитивы, capability negotiation.
- [Anthropic — Introducing MCP](https://www.anthropic.com/news/model-context-protocol) — зачем нужен стандарт.
- [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) — готовые серверы-примеры.
- [MCP — Architecture overview](https://modelcontextprotocol.io/docs/learn/architecture) — официальная страница по теме урока: host/client/server, примитивы (tools/resources/prompts), capability negotiation, JSON-RPC, транспорты.
- [DeepLearning.AI — MCP: Build Rich-Context AI Apps with Anthropic](https://learn.deeplearning.ai/courses/mcp-build-rich-context-ai-apps-with-anthropic) — бесплатный курс от Anthropic (Elie Schoppik): архитектура → свой сервер → подключение.
- [MCP Blog — One Year of MCP (релиз спеки 2025-11-25)](https://blog.modelcontextprotocol.io/posts/2025-11-25-first-mcp-anniversary/) — что нового и куда развивается протокол (Tasks и др.).
- [Rick Hightower — Claude and MCP: Content-Based Tool Integration (Medium)](https://medium.com/@richardhightower/anthropics-claude-and-mcp-a-deep-dive-into-content-based-tool-integration-dcf18cba82f0) — техническое сравнение подходов (Claude как content items vs OpenAI function calls).

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
