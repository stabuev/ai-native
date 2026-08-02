# Урок 6.2 · Архитектура MCP

**Фаза 6 — Инструменты и протоколы (MCP)** · **Результат фазы:** объяснить tool use
изнутри и поднять собственный MCP-сервер с контролем доступа.

**Результат урока:** после урока ты сможешь разложить рабочую интеграцию на
`host → client → server`, обоснованно выбрать `tool`, `resource` или `prompt` для
каждой возможности и проследить один вызов от модели до MCP-сервера и обратно, не
смешивая идентификаторы и уровни протокола.

**Опоры:** tool spec, локальный registry, `tool_call`, `tool_result`, allowlist и
call ID из 6.1. API-ключи, сеть и установленный MCP-клиент не нужны. Основной маршрут
опирается на актуальную ревизию MCP `2026-07-28`; прежний handshake упомянут только как
граница совместимости.

Дальше **capability** называем одну публикуемую возможность server: tool, resource или
prompt. **Descriptor** — её публичное машинно-читаемое описание: имя, назначение, входы,
выходы и другие metadata, но не сама скрытая реализация.

> **MOTTO.** MCP не даёт модели новые способности сам по себе. Он задаёт общий
> контракт, по которому приложение обнаруживает и использует возможности серверов.

## От локального runtime к переносимой границе

В 6.1 всё находилось в одном приложении:

```text
user request
    ↓
model + public tool specs
    ↓ tool_call
local registry → validation → Python callable
    ↓ tool_result
model → final answer
```

Такой runtime уже безопаснее прямого вызова функции, но его public specs и callable
всё ещё «вшиты» в конкретное приложение. Если один и тот же read-only
`get_release_decision` нужен в IDE, desktop-ассистенте и внутреннем агенте, придётся
поддерживать несколько адаптеров, способов запуска и форматов конфигурации.

MCP переносит границу:

| В 6.1 | В MCP-интеграции |
|---|---|
| public spec хранит приложение | server публикует descriptor через `tools/list` |
| callable находится в local registry | реализация остаётся внутри MCP server |
| runtime выбирает callable по allowlist | host маршрутизирует вызов через нужный MCP client |
| локальный `dispatch` возвращает результат | client вызывает `tools/call` и получает MCP result |
| provider call ID связывает call/result | host дополнительно связывает его с ID MCP-запроса |

Перед чтением дальше сделай прогноз:

> Если один MCP-сервер публикует десять инструментов, а host подключён к трём
> серверам, сколько MCP clients находится внутри host: один, три или тридцать?

К ответу вернёмся после разбора ролей.

## Пять участников, а не три взаимозаменяемых слова

Сначала обычным языком:

- **пользователь** ставит задачу и видит интерфейс приложения;
- **модель** предлагает текст или вызов доступного инструмента;
- **host** — само AI-приложение: оно управляет моделью, политиками и подключениями;
- **MCP client** — компонент host, который поддерживает одну протокольную связь с конкретным server;
- **MCP server** — отдельная программа или сервис, публикующий возможности и исполняющий разрешённые запросы.

```text
Пользователь
    ↓ задача / подтверждение
Host — AI-приложение
├── model adapter + conversation
├── policy / approvals / unified registry
├── MCP client A ⇄ MCP server A
└── MCP client B ⇄ MCP server B
```

Host создаёт отдельный MCP client для каждого подключённого server. Поэтому в вопросе
выше правильный ответ — **три clients**, а не один и не тридцать. Это связь «один
client target ↔ один server», а не утверждение, что server способен обслуживать только
одного клиента вообще. Локальный STDIO-server обычно обслуживает запустивший его client,
а удалённый HTTP-server может одновременно обслуживать много клиентов разных hosts.

### Что делает host

MCP не определяет, какую модель использовать и как строить интерфейс. Это ответственность
host. Обычно он:

1. читает конфигурацию подключений;
2. создаёт MCP clients;
3. договаривается с servers о поддерживаемых возможностях;
4. собирает descriptors из подключений в единый registry;
5. передаёт подходящие specs модели;
6. применяет локальные политики и подтверждения;
7. маршрутизирует запрос нужному server;
8. переводит MCP result обратно в формат model provider.

### Что делает client

Client знает протокол для одного server: обнаруживает поддерживаемые версии и
capabilities, добавляет protocol metadata в запросы и сопоставляет JSON-RPC
request/response. Client не является второй моделью и сам не решает бизнес-задачу.

### Что делает server

Server публикует только собственный контракт и исполняет собственную реализацию. Он может
работать локально или удалённо и не обязан знать, какая LLM находится в host. Граница
server — одновременно граница домена и доверия: открытые им данные и операции становятся
доступны подключённым hosts в пределах их политик.

## Два слоя MCP

Слово «протокол» легко ошибочно свести к способу передать байты. В MCP разделены два
слоя:

| Слой | За что отвечает | Примеры |
|---|---|---|
| **Data layer** | смысл и форма сообщений | JSON-RPC 2.0, stateless requests, version/capability metadata, tools/resources/prompts |
| **Transport layer** | как сообщения перемещаются между процессами | STDIO, Streamable HTTP, framing и транспортная авторизация |

JSON-RPC — основа обмена сообщениями в data layer, а не отдельный MCP-транспорт. В 6.3
ты увидишь envelopes `server/discover`, `tools/list` и `tools/call` и реализуешь server.
В 6.4 подключишь transports и проверишь реальную связь.

## Stateless core: сначала discover, затем self-contained request

Начиная с MCP `2026-07-28`, протокольного handshake и session state нет. Каждый request
сам несёт необходимые metadata: версию протокола, сведения о client и актуальные client
capabilities. Server не должен восстанавливать смысл запроса из предыдущих сообщений на
том же соединении.

```text
1. host создаёт client для известного server target
2. client → server: server/discover + per-request _meta
3. server → client: supportedVersions + capabilities + serverInfo
4. client → server: tools/list / resources/list / prompts/list + per-request _meta
5. client → server: tools/call / resources/read / prompts/get + per-request _meta
```

`server/discover` отвечает на вопрос «какие версии и части протокола поддерживает этот
server». `tools/list` отвечает на другой вопрос: «какие именно tools сейчас доступны».
Нельзя использовать prompt только потому, что MCP вообще знает о prompts: server должен
объявить соответствующую capability, а client/host — уметь её использовать.

Для клиента `server/discover` опционален: он может сразу отправить self-contained request
и обработать ошибку несовместимой версии. В учебном trace мы вызываем discovery явно,
потому что так compatibility preflight наблюдаем и потому что этот probe помогает SDK
отличить современный server от legacy-server на STDIO.

Ревизия `2025-11-25` и более старые servers используют `initialize` →
`notifications/initialized`. Современный SDK может договориться о legacy-режиме сам; в
уроке не нужно вручную смешивать два wire protocol. В 6.3 ориентируйся на Python SDK 2.x,
который поддерживает и текущую, и прежние ревизии.

Здесь **discovery** означает получение protocol metadata и перечисление primitives уже
известного server. Поиск и установка публикации из MCP Registry — отдельная задача
распространения, а не замена `server/discover` и `*/list`.

## Tool, resource или prompt

Это не три формата одного объекта. Они различаются тем, **что представляют** и **кто
инициирует использование**.

| Primitive | Интуитивный вопрос | Кто обычно инициирует | Пример |
|---|---|---|---|
| **tool** | Нужно исполнить операцию с аргументами? | модель предлагает вызов; host разрешает и маршрутизирует | запросить решение запуска, посчитать метрику, создать задачу |
| **resource** | Это адресуемые данные, которые приложение получает как контекст? | приложение или пользователь выбирает источник | схема БД, policy document, запись по URI |
| **prompt** | Это явно выбираемый шаблон взаимодействия или workflow? | пользователь через UI/команду | «провести review запуска» с аргументом `run_id` |

### Tool не обязан изменять мир

Tool — исполняемая функция, а не синоним побочного эффекта. Он может быть:

- read-only: `get_release_decision(run_id)`;
- вычислительным: `calculate_margin(revenue, cost)`;
- изменяющим состояние: `create_ticket(title)`.

MCP допускает annotations вроде `readOnlyHint`, `destructiveHint` и
`idempotentHint`, но это подсказки, а не доказательство безопасности. Allowlist,
авторизацию и подтверждения всё равно контролируют server и host; детально это будет в
6.5.

### Resource — адресуемый контекст

Resource имеет URI и содержимое с типом данных. Бывают фиксированные resources и
resource templates с параметрами URI. Host может показать их пользователю, выбрать
нужное содержимое и поместить его в контекст модели.

Resource часто читается без побочного эффекта, но «read-only» само по себе ещё не делает
любой lookup ресурсом. Если модели нужно сформировать аргументы и запросить вычисление,
tool может быть естественнее.

### Prompt — не просто строка в реестре

Prompt — переиспользуемый параметризованный шаблон сообщений. Обычно пользователь явно
выбирает его в UI или командой. Server возвращает готовую структуру сообщений, а host
решает, как включить её в разговор.

## Неоднозначный выбор: одно содержание, разные поверхности

Возьмём решение quality gate из Фазы 5.

**Вариант A — tool:**

```text
get_release_decision(run_id)
```

Подходит, когда пользователь задаёт вопрос естественным языком, модель извлекает
`run_id`, а server выполняет динамический lookup. Tool остаётся read-only.

**Вариант B — resource template:**

```text
release://runs/{run_id}/decision
```

Подходит, когда решение является адресуемым документом, host или пользователь уже знает
его URI и хочет добавить содержимое в контекст.

**Вариант C — prompt:**

```text
review_release(run_id)
```

Подходит для явно запускаемого workflow: получить решение, проверить failed checks и
составить review. Prompt не хранит само решение и не исполняет lookup вместо tool.

Выбор определяется не аналогией GET/POST, а желаемым интерфейсом, владельцем инициативы
и формой результата. Иногда server оправданно публикует и resource, и tool над одной
доменной областью — если они поддерживают разные способы работы, а не дублируют друг
друга без причины.

## Полный trace: от вопроса до ответа

Пользователь спрашивает: «Какое решение у запуска
`phase-5-paid-revenue-q2`?» Server `analytics-quality` уже известен host.

```text
1. MCP client → analytics-quality:
   JSON-RPC request(id=40, method="server/discover",
                    _meta={protocolVersion: "2026-07-28", clientCapabilities: ...})

2. analytics-quality → MCP client:
   JSON-RPC response(id=40,
                     result={supportedVersions: [...], capabilities: {tools: ...}})

3. MCP client → analytics-quality:
   JSON-RPC request(id=41, method="tools/list",
                    _meta={protocolVersion: "2026-07-28", clientCapabilities: ...})

4. analytics-quality → MCP client:
   JSON-RPC response(id=41,
                     result={tools: [{name: get_release_decision,
                                      description: ..., inputSchema: ...}]})

5. host:
   нормализует descriptor в provider tool spec и передаёт модели

6. model → host:
   provider tool_call(id="call-release-1",
                      name="get_release_decision",
                      arguments={run_id: "phase-5-paid-revenue-q2"})

7. host:
   находит server-владельца и создаёт MCP request

8. MCP client → analytics-quality:
   JSON-RPC request(id=42, method="tools/call",
                    params={name: ..., arguments: ...},
                    _meta={protocolVersion: "2026-07-28", clientCapabilities: ...})

9. analytics-quality → MCP client:
   JSON-RPC response(id=42, result={resultType: "complete", content: ...})

10. host → model:
   provider tool_result(call_id="call-release-1", content=...)

11. model → user:
   «Решение: publish ...»
```

Здесь два разных уровня корреляции:

| ID | Что связывает | Кто им управляет |
|---|---|---|
| `call-release-1` | model tool call ↔ provider tool result | adapter разговора внутри host |
| `42` | MCP JSON-RPC request ↔ MCP response | MCP client |

Они могут случайно выглядеть одинаково, но полагаться на это нельзя. Host хранит явное
соответствие между двумя уровнями. Именно этот adapter превращает tool use из 6.1 в
вызов внешнего MCP-server.

## Граница обещания MCP

MCP уменьшает число уникальных интеграций, но не гарантирует, что любой server заработает
в любом host без условий. Для совместимости должны совпасть:

- поддерживаемая версия протокола и нужные capabilities;
- transport, который умеют обе стороны;
- схема авторизации и доступные credentials;
- политика host: разрешён ли server и конкретная операция;
- используемые extensions и форматы content;
- доступность самого server и его зависимостей.

Корректная формулировка поэтому такая: **один MCP-server можно переиспользовать в разных
совместимых hosts через общий протокол**, а не «любой server автоматически работает
везде».

## САМОСТОЯТЕЛЬНАЯ ПРАКТИКА — спроектируй границу

Здесь не нужно заново программировать registry: это не доказало бы архитектурное
решение и забрало бы работу у 6.3. Открой раздел `Handoff в 6.2` своего
`6.1-tool-use/tool-contract-and-trace.md` и разложи **тот же пользовательский сценарий и
собственный read-only инструмент** на участников, primitives и два уровня trace.

Не возвращайся к reference `get_release_decision`, если в 6.1 уже сделал собственный
перенос. Две дополнительные возможности для классификации можно предложить рядом с
первой: например, адресуемый policy document или явно запускаемый review prompt. Они
помогают понять границу primitives, но реализовывать в 6.3 нужно только одну capability.

Создай личную папку с нуля — репозиторий курса клонировать не требуется:

```text
ai-native-work/
└── course-work/
    └── phase-6/
        └── 6.2-mcp-architecture/
            └── mcp-boundary-and-traces.md
```

Заполни [шаблон артефакта](#lesson-files):

1. зафиксируй путь к артефакту 6.1 и что именно переносишь без изменения;
2. назови пользователя, host и доменную границу будущего server;
3. перечисли связи client ↔ server — по одному client target на server;
4. классифицируй capability 6.1 и ещё две правдоподобные возможности, не заставляя себя использовать все primitives;
5. для одного неоднозначного выбора объясни, почему отвергнуты альтернативы;
6. построй успешный trace от `server/discover` до ответа пользователю;
7. явно раздели provider call ID и MCP JSON-RPC ID;
8. сломай одно условие совместимости и покажи, где отказ обнаруживается до исполнения;
9. выбери capability 6.1 первой для реализации в 6.3 или обоснуй конкретную несовместимость и минимальное изменение контракта.

### Если делегируешь черновик ИИ

Используй 4D как рамку качества:

- **Delegation:** отдай черновую классификацию и поиск неоднозначных мест, но не окончательное решение о границе server.
- **Description:** передай реальные hosts, данные, операции, владельца инициативы, read/write-эффект и ограничения доступа.
- **Discernment:** проверь, не назван ли любой read-only lookup ресурсом, не перепутаны ли host и client и не склеены ли два ID.
- **Diligence:** сверяй спорные поля с официальной документацией и заполни failure trace, а не ограничивайся красивой схемой.

## SHIP IT — карта границ и два trace

Артефакт урока —
[`outputs/mcp-boundary-and-traces.md`](../outputs/mcp-boundary-and-traces.md). Он станет
входом 6.3: там ты превратишь capability из 6.1 в первый tool, resource или prompt
работающего MCP-server. Если primitive или contract пришлось изменить, артефакт должен
сохранить причину, а не скрыть разрыв новым примером.

Перед завершением проверь артефакт по рубрике:

- пользователь, model, host, clients и servers не смешаны;
- primitive выбран по форме взаимодействия и владельцу инициативы, а не только по read/write;
- trace показывает `server/discover`, per-request metadata, `*/list` и фактическое использование;
- provider call ID не выдан за MCP request ID;
- failure обнаруживается в конкретной точке и не скрывается общим словом «ошибка»;
- задача, public contract и evidence из 6.1 явно сопоставлены с новой MCP-границей;
- граница server достаточно связная, чтобы реализовать её в 6.3.

## ЧАСТЫЕ ОШИБКИ

- **Называть host моделью.** Модель — компонент; host управляет разговором, подключениями, политиками и переводом форматов.
- **Считать один client общим для всех servers.** Host создаёт отдельный client target для каждого server.
- **Считать tool обязательно мутирующим.** Запрос к БД и вычисление тоже могут быть tools; эффект описывается отдельно.
- **Считать любой read-only объект resource.** Resource — адресуемый контекст; модельно инициируемый lookup может оставаться tool.
- **Путать JSON-RPC и transport.** Первый задаёт сообщения, второй переносит их между процессами.
- **Переносить session state из старой ревизии.** В `2026-07-28` каждый request self-contained; server не полагается на прежний handshake.
- **Считать `server/discover` списком tools.** Он сообщает versions/capabilities; конкретные descriptors приходят из `*/list`.
- **Склеивать provider call ID и JSON-RPC ID.** Они коррелируют разные пары событий.
- **Обещать универсальную совместимость.** Host всё равно должен поддерживать нужный transport, capability, auth и policy.
- **Подключать случайный server ради упражнения.** Архитектурный результат полностью проверяется офлайн; подключение и инспекция будут в 6.4.

## ЧТО СОЗНАТЕЛЬНО НЕ ВХОДИТ В УРОК

- точные JSON-RPC envelopes и обработчик server — 6.3;
- STDIO, Streamable HTTP, Inspector и подключение к host — 6.4;
- авторизация, approvals, least privilege и изоляция — 6.5;
- multi round-trip requests, `subscriptions/listen`, elicitation и extensions;
- legacy-handshake старых ревизий, migration internals и registry/distribution инфраструктура.

## ПРОВЕРЬ СЕБЯ

Вопросы ниже проверяют выбор primitive, границы участников, capabilities и корреляцию
двух протокольных уровней, а не память о расшифровке MCP.

{{quiz}}

## Дополнительное чтение

Читать всё не требуется. Выбери одну ветку: уточнить архитектуру, понять переход между
ревизиями, подготовиться к Python SDK 2.x или посмотреть распространение servers.

**Уточнить текущий архитектурный контракт**

- [MCP — Architecture overview](https://modelcontextprotocol.io/docs/learn/architecture) — прочитай Participants, Layers и Data layer walkthrough: сопоставь официальную схему с собственной картой host/client/server и проверь границу JSON-RPC/transport.
- [MCP Specification 2026-07-28 — Overview](https://modelcontextprotocol.io/specification/2026-07-28) — открой Base Protocol и Features: это источник точных требований для stateless requests, per-request capabilities и tools/resources/prompts.
- [MCP Specification — Server discovery](https://modelcontextprotocol.io/specification/2026-07-28/server/discover) — разберись, чем `server/discover` отличается от `tools/list` и публичного MCP Registry; особенно полезно для compatibility preflight артефакта.

**Понять смену ревизии без изучения всей истории**

- [MCP Blog — 2026-07-28 Release Candidate explainer](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/) — прочитай Stateless protocol core и The handshake and session are gone: авторы спецификации объясняют, почему `initialize` из ревизии `2025-11-25` больше не является текущей основной моделью.
- [MCP Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25) — открывай только при разборе legacy-server или SDK 1.x: сравни stateful connections и initialization с текущим per-request контрактом, не смешивая payload двух ревизий.

**Подготовиться к реализации 6.3**

- [MCP Python SDK v2](https://github.com/modelcontextprotocol/python-sdk) — пройди A server in 15 lines и A client in 10 lines: v2 поддерживает `2026-07-28` и прежние ревизии, а текущий server API использует `MCPServer` вместо учебного ручного dispatcher.
- [MCP Python SDK v2.0.0 release](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.0.0) — прочитай One SDK, both protocol eras и migration highlights, чтобы отличить текущий SDK от ветки 1.x в maintenance mode.

**Посмотреть происхождение и распространение экосистемы**

- [Anthropic — Introducing MCP](https://www.anthropic.com/news/model-context-protocol) — исторический анонс 2024 года: полезен для мотивации N×M интеграций, но не является источником текущего wire contract.
- [Official MCP Registry](https://registry.modelcontextprotocol.io/) — посмотри, как servers публикуются и находятся пользователями; это distribution discovery, а не `server/discover` внутри протокола.
- [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) — изучи `Everything` или один небольшой reference server как пример primitives; README прямо предупреждает, что эти реализации учебные, а не production-ready.

---
**Часы:** ~4 · **DoD:** студент обоснованно классифицирует собственные возможности как
tool/resource/prompt; корректно разделяет user/model/host/client/server, data и transport
layers, `server/discover` и primitive listing; успешный trace связывает provider call с
MCP request через два разных ID; failure trace показывает точку безопасного отказа;
заполненная карта задаёт реализуемую server boundary для 6.3. ✅ **Урок готов**
