# Урок 6.3 · Свой MCP-сервер на Python SDK

**Фаза 6 — Инструменты и протоколы (MCP)** · **Результат фазы:** объяснить tool use
изнутри и поднять собственный MCP-сервер с контролем доступа.
<!-- exercise -->

**Результат урока:** после урока ты сможешь превратить выбранную в 6.2 capability в
работающий `MCPServer` на Python SDK 2.x и через in-memory client доказать, что server
публикует ожидаемый descriptor, выполняет допустимый вызов и безопасно отклоняет
некорректный.

**Опоры:** public tool contract, validation и dispatch из 6.1; граница server, выбор
tool/resource/prompt и первая capability из артефакта 6.2.

**Requires:** Python 3.10+, `uv` и однократный доступ к сети для установки
`mcp>=2,<3`. API-ключ, LLM, отдельный MCP-host, порт и внешняя БД не нужны. После
установки зависимостей основная практика и тесты работают локально без сети.

> **MOTTO.** SDK берёт на себя протокол. Ты отвечаешь за честную capability и
> доказательства её поведения.

## От архитектурной карты к работающей границе

В конце 6.2 у тебя остались не абстрактные слова об MCP, а конкретный handoff:

```text
одна server boundary
+ первая capability
+ выбранный primitive
+ безопасная локальная fixture
+ ожидаемый успешный и отказной trace
```

Теперь эту спецификацию нужно превратить в исполняемую программу. В reference-сценарии
server `analytics-quality` публикует read-only tool:

```text
get_release_decision(run_id)
→ {run_id, decision, reason}
```

Он читает зафиксированные решения quality gate из безопасного словаря, а не подключается
к рабочей БД. Это уже не игрушечное `add(2, 3)`: у capability есть предметный вход,
структурированный результат и правдоподобная ошибка — неизвестный `run_id`.

После reference-прогона ты заменишь эту границу первой capability из своей карты 6.2.
Если там выбран resource или prompt, не превращай его в tool ради совпадения с примером:
перенеси тот же способ проверки на подходящий primitive.

## Что именно строит автор server, а что делает SDK

В актуальной линии [MCP Python SDK 2.x](https://github.com/modelcontextprotocol/python-sdk)
основной класс server называется `MCPServer`. Минимальная регистрация tool выглядит
так:

```python
from mcp.server import MCPServer

mcp = MCPServer("analytics-quality")

@mcp.tool()
def get_release_decision(run_id: str) -> dict[str, str]:
    """Return the recorded quality-gate decision for one local run ID."""
    ...
```

Строка с `@mcp.tool()` называется **декоратором**: она регистрирует следующую функцию
как публичную MCP-capability. Символ `...` здесь означает место реализации в объяснении,
а не заглушку в итоговом файле — рабочее решение будет полноценным.

Граница ответственности разделяется так:

| Автор server задаёт | SDK строит или обрабатывает |
|---|---|
| связную доменную границу | MCP discovery и protocol metadata |
| public name и точное описание | JSON-RPC framing и correlation request/response |
| типы входов и выхода | `inputSchema` и `outputSchema` |
| domain handler | проверку аргументов до вызова handler |
| предметный успех и ожидаемые ошибки | `content`, `structuredContent` и tool-error result |
| безопасный источник данных | подключение in-memory client к server object |

В 6.1 ручной registry и dispatcher уже показали, зачем перед исполнением нужны public
spec, allowlist и validation. Повторно писать неполный MCP-dispatcher здесь не нужно:
это научило бы поддерживать копию протокола, а не строить собственный server.

## Как функция превращается в публичный контракт

Рассмотрим четыре части функции до запуска кода.

### 1. Имя

Имя `get_release_decision` становится public tool name. Его увидят client, host и
модель. Имя должно описывать одно действие; `run`, `query` или `helper` не объясняют
потребителю, что произойдёт.

### 2. Docstring

Строка сразу под сигнатурой называется **docstring**. SDK использует её как описание
tool. Это не комментарий только для разработчика: описание попадёт в descriptor,
который host покажет модели.

Плохое описание:

```text
Get data.
```

Проверяемое описание:

```text
Return the recorded quality-gate decision for one local run ID.
```

Второе называет объект, действие и границу источника: уже записанное локальное решение,
а не произвольный запрос к миру.

### 3. Type hints

Запись `run_id: str` — **type hint**, то есть объявленный тип аргумента. В обычном
Python это прежде всего подсказка инструментам разработки; в MCP SDK она становится
частью исполняемого контракта. Из сигнатуры SDK строит JSON Schema, упрощённо:

```json
{
  "type": "object",
  "properties": {"run_id": {"type": "string"}},
  "required": ["run_id"]
}
```

Аргумент попал в `required`, потому что у него нет default value. Если написать
`run_id: str = "latest"`, SDK объявит аргумент необязательным. Это уже изменение
публичного поведения, а не косметический Python-синтаксис.

### 4. Return type

Чтобы результат был машинно-проверяемым, reference-server возвращает не свободную
строку, а `ReleaseDecision` — `TypedDict` с тремя полями:

```python
class ReleaseDecision(TypedDict):
    run_id: str
    decision: Literal["publish", "review", "block"]
    reason: str
```

`TypedDict` описывает форму обычного словаря, а `Literal` ограничивает допустимые
решения тремя значениями. SDK строит из return type `outputSchema`, проверяет
возвращённое значение и заполняет два канала результата:

- `content` — текстовые блоки, которые может прочитать модель;
- `structured_content` — данные, которые без разбора текста использует host.

Значит, type hints — не обещание «для красоты». Они влияют на то, какой ввод server
примет и какой результат разрешит вернуть.

## Полный путь одного вызова

Сначала сделай прогноз: если client забудет `run_id`, успеет ли функция
`lookup_release_decision()` обратиться к словарю?

Теперь проследим путь:

```text
1. Client подключается к объекту MCPServer в памяти.
2. SDK сообщает capabilities server и отдаёт descriptor через tools/list.
3. Client вызывает get_release_decision с arguments.
4. SDK сверяет arguments с generated inputSchema.
5. Только после успешной проверки вызывается get_release_decision(...).
6. Domain handler читает локальную fixture.
7. SDK сверяет return value с outputSchema.
8. Client получает content + structured_content или наблюдаемую ошибку.
```

Ответ на прогноз: **нет**. Отсутствующий обязательный аргумент отклоняется на шаге 4,
до domain handler. В тесте мало проверить только `is_error=True`: мы подменим lookup
функцией, которая немедленно упадёт при вызове. Если тест останется зелёным, значит
невалидный input действительно не пересёк доменную границу.

### Почему client здесь асинхронный

Даже in-memory client использует тот же асинхронный интерфейс, что и реальные
подключения:

```python
async with Client(mcp) as client:
    result = await client.call_tool("get_release_decision", {"run_id": "..."})
```

`async with` открывает и гарантированно закрывает временное подключение, а `await`
означает «приостановить текущий сценарий, пока операция не завершится». Порта и отдельного
процесса при этом нет: `Client(mcp)` обращается прямо к server object. В тестах
`pytest.mark.anyio` позволяет pytest выполнить такую `async def` функцию.

## Ошибка tool и ошибка протокола — не одно и то же

Для reference-сценария важны три разных исхода:

| Ситуация | Дошла ли до handler | Что наблюдает client |
|---|---:|---|
| нет обязательного `run_id` | нет | tool result с `is_error=True` и сообщением validation |
| `run_id` корректного типа, но записи нет | да | обычное исключение превращается в `is_error=True`; модель может исправить ID и повторить |
| сам request нельзя обслужить из-за протокольного условия | зависит от точки отказа | `MCPError`: весь MCP request завершается protocol error |

Не возвращай строку `"ERROR: run not found"`. Для client это успешный результат с
`is_error=False`, поэтому ошибка маскируется под данные. Восстановимый предметный miss
нужно выражать обычным исключением. `MCPError` нужен значительно реже — когда новый
аргумент модели не исправит сам request, например client не объявил обязательную
capability.

## BUILD IT — рабочий server и поведенческие доказательства

### 1. Создай проект с нуля

Репозиторий курса клонировать не требуется. Работай в личной истории из Фазы 0:

```bash
mkdir -p ai-native-work/course-work/phase-6/6.3-mcp-server
cd ai-native-work/course-work/phase-6/6.3-mcp-server
uv init --python 3.12
uv add "mcp>=2,<3"
uv add --dev pytest
mkdir -p code
```

Скопируй из блока [«Исходники урока»](#lesson-files) в `code/` два файла:

- `release_decision_server.py` — эталонное имя реализации;
- `test_release_decision_server.py` — тесты как исполняемое ТЗ.

Если собираешь самостоятельно или делегируешь черновик ИИ, сначала возьми только тесты
и спецификацию ниже. Эталонное решение остаётся под катом.

### 2. Реализуй контракт

В `release_decision_server.py` должны появиться:

#### `ReleaseDecision`

- **Вход:** классу вход не передаётся; он объявляет форму результата.
- **Действие:** задаёт поля `run_id`, `decision`, `reason`; `decision` допускает только `publish`, `review`, `block`.
- **Выходной инвариант:** return annotation tool позволяет SDK построить `outputSchema` с тремя обязательными полями.

#### `lookup_release_decision(run_id: str) -> ReleaseDecision`

- **Вход:** строковый ID запуска.
- **Действие:** ищет запись только в безопасной локальной fixture.
- **Успех:** возвращает копию найденной записи.
- **Ошибка:** для неизвестного ID выбрасывает `ValueError` с самим ID, но без внутренних путей, секретов и стектрейса.

#### `mcp = MCPServer("analytics-quality")`

- создаёт server object с одной связной доменной ответственностью;
- не запускает порт и не выбирает transport — это будет в 6.4.

#### `get_release_decision(run_id: str) -> ReleaseDecision`

- зарегистрирован через `@mcp.tool()`;
- имеет точный docstring для descriptor;
- помечен annotations как read-only и closed-world;
- передаёт корректный input в domain lookup и возвращает структурированный результат;
- не дублирует schema validation внутри handler.

#### `_demo()`

- открывает `Client(mcp, raise_exceptions=True)` in-memory;
- получает список tools;
- вызывает `get_release_decision` на известной fixture;
- печатает public name и `structured_content`.

`raise_exceptions=True` помогает тестам показать неожиданные сбои вокруг handler, но не
превращает обычный tool error обратно в Python traceback: ожидаемый miss всё равно нужно
проверять через `result.is_error`.

### 3. Пройди red → green

```bash
uv run pytest code -q
uv run python code/release_decision_server.py
```

**Готово, когда четыре теста зелёные:**

1. listing показывает осмысленный descriptor и generated input/output schemas;
2. допустимый вызов возвращает точный structured domain result;
3. schema-invalid input даёт `is_error=True` и не вызывает domain lookup;
4. неизвестный `run_id` даёт восстанавливаемый tool error, а не ложный успех.

Тест прямого вызова `get_release_decision(...)` был бы полезен для domain logic, но его
одного недостаточно: он обошёл бы MCP descriptor, schema validation и result envelope.

## Перенеси первую capability из 6.2

Reference-server доказывает механизм. Результат урока появляется после переноса на твою
границу.

1. Открой раздел `Handoff в 6.3` в своём `mcp-boundary-and-traces.md`.
2. Оставь только безопасную fixture или adapter — без рабочего секрета и production write.
3. Замени имя, docstring, input и output contracts на собственные.
4. Перепиши expected values теста до реализации, чтобы тест задавал поведение, а не повторял уже написанный код.
5. Добавь один реалистичный failure case своей области.
6. Снова получи red, реализуй минимальное изменение и верни green.

Если в 6.2 выбран другой primitive, меняется поверхность проверки:

| Primitive | Что публикуем | Что проверяем in-memory |
|---|---|---|
| tool | исполняемая операция с аргументами | descriptor, `call_tool`, structured result и tool error |
| resource | адресуемые данные или URI template | descriptor/template, `read_resource`, содержимое и отсутствующий URI |
| prompt | выбираемый пользователем шаблон | descriptor, `get_prompt`, аргументы и полученные messages |

Не добавляй остальные два primitives только ради заполнения таблицы. Один честно
выбранный и проверенный primitive лучше трёх декоративных.

### Если делегируешь реализацию ИИ

Используй 4D не как лозунг, а как процедуру приёмки:

- **Delegation:** отдай черновик функции, fixture и тестов; решение о server boundary и допустимых данных оставь за собой.
- **Description:** передай артефакт 6.2, точные input/output contracts, SDK `>=2,<3`, ожидаемые ошибки и запрет на сеть, secrets и лишние primitives.
- **Discernment:** сравни generated descriptor с намерением. Рабочая Python-функция с неверным docstring, optional input или свободной строкой вместо структуры не проходит.
- **Diligence:** прочитай diff, запусти все четыре behavioural tests, воспроизведи отказ, проверь `uv.lock` и поиском убедись, что в проект не попали credentials.

ИИ может ускорить набор кода, но не может доказать корректность фразой «готово». В этой
задаче доказательство — наблюдаемое поведение через независимый client.

## SHIP IT — проверенный server и build record

Скопируй и заполни
[`outputs/mcp-server-build-record.md`](../outputs/mcp-server-build-record.md). В личном
проекте после урока должны остаться:

```text
6.3-mcp-server/
├── pyproject.toml
├── uv.lock
├── code/
│   ├── <your_server>.py
│   └── test_<your_server>.py
└── mcp-server-build-record.md
```

Build record связывает решение 6.2, фактический descriptor, успешный вызов, безопасный
отказ и команды воспроизведения. В 6.4 к нему добавятся Inspector, transport и
подключение к выбранному host; в 6.5 — контроль доступа и проверка открытой поверхности.

Перед завершением проверь:

- server реализует именно выбранную границу, а не несвязанный demo;
- public name и description понятны без чтения исходного кода;
- schema отражает реальные обязательные поля и ограничения;
- structured result соответствует предметному контракту;
- ожидаемый miss наблюдаем как ошибка и не выдаётся за успех;
- tests проходят из записанного окружения;
- in-memory green не объявлен доказательством транспорта или безопасности.

## ЧАСТЫЕ ОШИБКИ

- **Использовать старый `FastMCP` import и вручную требовать `initialize`.** Основной маршрут урока — `MCPServer` SDK 2.x и [текущий stateless protocol](https://modelcontextprotocol.io/specification/2026-07-28); legacy оставь SDK.
- **Тестировать только Python-функцию.** Такой тест не видит descriptor, generated schema, MCP validation и result envelope.
- **Считать type hints комментариями.** Default value меняет `required`, неверный тип меняет публичный контракт, а return annotation определяет output schema.
- **Возвращать ошибку строкой.** Client пометит её успехом. Для восстанавливаемого miss выбрасывай обычное исключение и проверяй `is_error=True`.
- **Ловить `Exception` и скрывать всё одним сообщением.** Так исчезает различие между ожидаемым domain miss и настоящим дефектом реализации.
- **Публиковать все primitives.** Capability существует для сценария, а не для демонстрации количества декораторов.
- **Смешивать application data и protocol session state.** Локальная fixture допустима; недопустимо выводить protocol version, client capabilities или identity из предыдущего request на соединении.
- **Считать in-memory green гарантией подключения.** Процесс, STDIO/HTTP, Inspector и конфиг host ещё не проверены — это граница 6.4.
- **Класть секрет в fixture или build record.** Учебному server достаточно синтетических данных; доступы и least privilege появятся в 6.5.

## ЧТО СОЗНАТЕЛЬНО НЕ ВХОДИТ В УРОК

- ручная реализация JSON-RPC и всех MCP methods;
- legacy-handshake и migration internals SDK 1.x;
- обязательная публикация tool, resource и prompt одновременно;
- STDIO, Streamable HTTP, MCP Inspector и конфигурация host — 6.4;
- auth, approvals, least privilege и изоляция — 6.5;
- реальная БД, внешняя сеть, production writes и secrets;
- low-level Server, middleware, subscriptions, elicitation и extensions.

## ПРОВЕРЬ СЕБЯ

Вопросы ниже проверяют generated contract, границу validation/handler, различие tool и
protocol error, ограничения in-memory теста и приёмку AI-сгенерированного server.

{{quiz}}

## Дополнительное чтение

Читать всё не требуется. Выбери одну ветку по своему вопросу: глубже понять generated contracts и ошибки, сверить их со спецификацией, разобраться с устройством async-тестов или сравнить официальный SDK с отдельным фреймворком FastMCP.

**Углубить механизм урока**

- [MCP Python SDK — Tools](https://py.sdk.modelcontextprotocol.io/servers/tools/) — открой The input schema, Optional arguments и Names, titles, and annotations: увидишь, как type hints, defaults и annotations превращаются в public descriptor и validation до handler.
- [MCP Python SDK — Structured Output](https://py.sdk.modelcontextprotocol.io/servers/structured-output/) — сравни `TypedDict`, dataclass и Pydantic model, затем прочитай Validation: это точный контракт `outputSchema`, `content` и `structured_content` из практики.
- [MCP Python SDK — Handling errors](https://py.sdk.modelcontextprotocol.io/servers/handling-errors/) — прочитай An error the model can fix, Which one to raise и Errors you never raise: раздел проводит границу между обычным исключением, tool error и `MCPError`.
- [MCP Python SDK — Testing](https://py.sdk.modelcontextprotocol.io/get-started/testing/) — открой Basic usage, Why `raise_exceptions=True`? и In-process by default: это официальный паттерн проверки server через `Client(mcp)` без процесса, порта и transport.

**Сверить реализацию со стандартом**

- [MCP Specification 2026-07-28 — Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) — используй как wire-level источник правды для `tools/list`, `tools/call`, schemas и результатов; полезно, если нужно отличить гарантии протокола от удобств Python SDK.

**Углубить механику тестов**

- [pytest — monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html) — раздел Monkeypatching functions объясняет подмену domain lookup, с помощью которой тест доказывает, что schema-invalid input не дошёл до handler.
- [AnyIO — Testing](https://anyio.readthedocs.io/en/stable/testing.html) — прочитай Creating asynchronous tests и Asynchronous fixtures: станет понятно, зачем тестам `pytest.mark.anyio`, `anyio_backend` и async client fixture.

**Сравнить с альтернативным Python-фреймворком**

- [FastMCP — Create an MCP Server in Python](https://gofastmcp.com/tutorials/create-mcp-server) — отдельная факультативная ветка после основного упражнения: сравни API пакета `fastmcp` с официальным `MCPServer`, но не смешивай зависимости и примеры двух библиотек в одном учебном server.

---
**Часы:** ~4 · **DoD:** студент превращает первую capability из 6.2 в `MCPServer`
SDK 2.x; listing подтверждает public descriptor и generated schemas; in-memory client
доказывает предметный успех, schema rejection до handler и восстанавливаемый domain
miss; личный server воспроизводится из lock-файла и передан в 6.4 через заполненный build
record. ✅ **Урок готов**
