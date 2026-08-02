# Урок 6.4 · От server object к Inspector и host

**Фаза 6 — Инструменты и протоколы (MCP)** · **Результат фазы:** объяснить tool use
изнутри и поднять собственный MCP-сервер с контролем доступа.

**Результат урока:** после урока ты сможешь взять проверенный in-memory server из 6.3,
запустить его через выбранный transport, исследовать реальную capability в официальном
MCP Inspector, подключить к одному совместимому host и по наблюдаемым свидетельствам
локализовать сбой между server, process/transport и host configuration.

**Роль в маршруте:** обязательный интеграционный мост между реализацией server в 6.3 и
проверкой его открытой поверхности и доступа в 6.5.

**Опоры:** личный `MCPServer`, зелёные behavioural tests и заполненный раздел `Handoff
в 6.4` из build record урока 6.3. Если этих трёх опор нет, сначала закончи 6.3: этот
урок не строит второй демонстрационный server взамен личного.

**Requires:** существующий проект `6.3-mcp-server`, Python 3.10+, `uv`, Node.js версии,
поддерживаемой текущим MCP Inspector, однократный доступ к сети для `mcp[cli]` и
Inspector, а также один доступный MCP-compatible host. API-ключ и рабочие секреты для
reference-server не нужны.

> **MOTTO.** Доказывай подключение по слоям: server → process/transport → Inspector →
> host. Один симптом — одна следующая гипотеза.

## Зачем нужен отдельный урок после зелёных тестов

В 6.3 client обращался прямо к объекту `MCPServer` в памяти:

```text
test process → Client(mcp) → server object
```

Эта проверка уже доказала важное: descriptor имеет ожидаемую форму, валидный вызов
возвращает правильный результат, а некорректный input или предметный miss не маскируется
под успех. Но она сознательно обошла четыре новых элемента:

```text
host → MCP client → process + transport → server
```

- **process** — отдельный запущенный экземпляр Python-программы;
- **transport** — правила доставки MCP messages между client и server;
- **host** — продукт, в котором работает пользователь и модель: например, desktop-приложение или coding agent;
- **configuration** — точная команда, аргументы, рабочая папка и environment, по которым host находит и запускает server.

Поэтому «тесты зелёные» и «инструмент появился в агенте» — разные утверждения. Урок 6.4
добавляет недостающие доказательства, не переписывая протокол и не дублируя server.

## Четыре роли в одном подключении

Слова `host` и `client` часто используют как синонимы, но для диагностики их полезно
разделять:

```text
пользователь
    │
    ▼
host: интерфейс агента, модель, approvals, список tools
    │ содержит
    ▼
MCP client: формирует MCP requests и читает responses
    │ transport
    ▼
server process: SDK + твоя capability + domain adapter
```

[MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) временно занимает
место client. Он подключается к server без модели и даёт вызвать tool, прочитать resource
или получить prompt вручную. Благодаря этому между server и сложным host появляется
наблюдаемая контрольная точка.

Inspector — инструмент интерактивного тестирования и отладки, а не сертификатор всей
реализации. Успешный прогон означает только следующее:

> выбранная capability была обнаружена и дала ожидаемые ответы в проверенном окружении
> через выбранный transport.

Он не доказывает полноту бизнес-логики, совместимость со всеми hosts, безопасность,
авторизацию или готовность к production.

## Transport: одна семантика, разные способы доставки

В [текущей transport specification](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports)
смысл requests не зависит от transport. Меняется то, как messages доставляются и как
живёт server process.

| Transport | Кто запускает server | Как передаются messages | Когда выбирать |
|---|---|---|---|
| STDIO | client/host запускает subprocess | `stdin` → server, `stdout` → client; logs идут в `stderr` | локальный server рядом с одним пользователем |
| Streamable HTTP | server запущен отдельно | HTTP POST к одному MCP endpoint; ответ — JSON или request-scoped SSE stream | самостоятельный сетевой сервис для удалённых clients |

Для личного локального server из 6.3 основной маршрут урока — **STDIO**. Он не требует
порта и отдельного deployment. Streamable HTTP выбирай только если в build record уже
есть реальная причина держать server как самостоятельно работающий HTTP-сервис.

У [STDIO](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio)
есть важный инвариант:

```text
stdout = только MCP messages
stderr = диагностические logs
```

Обычный `print()` в `stdout` может повредить framing: client попробует прочитать
человеческую строку как MCP message. Именно поэтому «скрипт запускается в терминале»
ещё не означает «STDIO transport работает».

## Диагностическая лестница

Не меняй код, transport и host config одновременно. Иди сверху вниз и переходи к
следующему слою только после наблюдаемого успеха предыдущего:

```text
1. In-memory tests 6.3 зелёные?
   ├─ нет → contract, schema, handler или domain fixture
   └─ да
      2. Inspector смог запустить process?
         ├─ нет → command, absolute path, cwd, dependency или environment
         └─ да
            3. Inspector обнаружил capability и вызвал её?
               ├─ нет → server entry point, transport/framing, SDK или public contract
               └─ да
                  4. Host увидел ту же capability?
                     ├─ нет → host config, restart, support или policy
                     └─ да
                        5. Тот же вызов дал ожидаемый результат?
                           ├─ нет → arguments, domain error, permission или host behaviour
                           └─ да → подключение доказано; доступ проверим в 6.5
```

Фраза «не работает MCP» слишком широкая. После этой лестницы диагноз должен звучать
наблюдаемо: «host не запускает subprocess, потому что в config относительный путь» или
«process запущен, descriptor виден, но schema отклоняет отсутствующий `run_id`».

## Практика: подключи server из 6.3

### 1. Верни известный зелёный baseline

Открой не репозиторий курса, а свой существующий проект:

```bash
cd ai-native-work/course-work/phase-6/6.3-mcp-server
uv run pytest code -q
uv run python code/release_decision_server.py
```

Не продолжай при красных тестах. Inspector добавит process и transport, но не исправит
сломанный descriptor или domain handler.

Запиши в будущий connection record:

- точную команду тестов и число прошедших тестов;
- имя public capability;
- один ожидаемый успешный input/output;
- один ожидаемый отказ;
- что этот baseline пока не проверил.

Для reference-server ожидаются tool `get_release_decision`, успешный
`run_id=phase-5-paid-revenue-q2` и предметный отказ на неизвестном `run_id`. Для личного
server возьми значения из своего build record, а не возвращай учебный пример.

### 2. Добавь development CLI в тот же проект

В 6.3 была нужна только основная SDK dependency. Для команды `mcp dev` добавь CLI extra
[официального Python SDK](https://github.com/modelcontextprotocol/python-sdk):

```bash
uv add "mcp[cli]>=2,<3"
node --version
npx --version
```

`uv add` обновит `pyproject.toml` и lock-файл существующего проекта. Новый проект и
вторая копия server не нужны. Если Inspector сообщает неподдерживаемую версию Node.js,
сверь минимальную версию в его текущем README и обнови Node до поддерживаемой линии.

### 3. Открой реальный server в Inspector

Из корня проекта 6.3 выполни:

```bash
uv run mcp dev code/release_decision_server.py
```

Команда SDK запускает development workflow с официальным MCP Inspector. Это уже не
`Client(mcp)` внутри тестового процесса: Inspector выступает отдельным client и
взаимодействует с реально запущенным server.

В интерфейсе сначала найди свой primitive:

- для tool — вкладка **Tools**;
- для resource — **Resources**;
- для prompt — **Prompts**.

Не требуй все три вкладки от каждого server. Сверяй только primitive, выбранный в 6.2
и реализованный в 6.3.

### 4. Проверь descriptor до вызова

Для reference-tool проверь:

- public name — `get_release_decision`;
- description объясняет, что возвращается записанное локальное решение;
- `run_id` имеет тип string и обязателен;
- output schema содержит `run_id`, `decision`, `reason`;
- annotations не обещают write или открытый внешний мир.

Для личной capability сравни Inspector не с исходным кодом, а с intent и expected
descriptor из build record. Ошибка в имени или required field — это дефект публичного
контракта, даже если handler можно вызвать напрямую из Python.

### 5. Вызови успех и ожидаемый отказ

Для reference-tool:

```json
{"run_id": "phase-5-paid-revenue-q2"}
```

В результате должны быть `decision: "publish"` и ожидаемая причина из безопасной fixture.
Затем передай:

```json
{"run_id": "phase-5-no-such-run"}
```

Второй вызов должен быть наблюдаемой tool error, а не успешной строкой, пустым ответом
или traceback с внутренними путями. Если в 6.3 выбран resource или prompt, выполни его
эквивалентные успешный и отказной сценарии из build record.

Сохрани не просто фразу «всё зелёное», а четыре свидетельства:

1. Inspector подключился к target;
2. descriptor совпал с intent;
3. известный input дал ожидаемый результат;
4. ожидаемый отказ остался безопасным и понятным.

### 6. Подготовь воспроизводимую STDIO-команду для host

`mcp dev` нужен для разработки. Host должен запускать server без Inspector, поэтому
его эквивалентная команда использует `mcp run`:

```bash
uv run mcp run code/release_decision_server.py
```

Host может стартовать из неизвестной рабочей папки и получить сокращённый `PATH`.
Поэтому в config используй абсолютный путь к `uv` и абсолютный путь к проекту.

Найди исполняемый файл:

```bash
command -v uv
```

В PowerShell используй `(Get-Command uv).Source`. Затем собери host-neutral STDIO entry:

```json
{
  "mcpServers": {
    "analytics-quality": {
      "command": "/absolute/path/to/uv",
      "args": [
        "--directory",
        "/absolute/path/to/ai-native-work/course-work/phase-6/6.3-mcp-server",
        "run",
        "mcp",
        "run",
        "code/release_decision_server.py"
      ]
    }
  }
}
```

Это смысловая форма, а не универсальный путь к настройкам: один host принимает JSON,
другой — CLI-команду, третий — поля формы. Перенеси **те же** `command` и `args` по
официальной инструкции выбранного host. Не угадывай расположение config и не смешивай
за один прогон инструкции Claude, Cursor, Codex и других продуктов.

В reference-сценарии переменные окружения не нужны. Не добавляй реальный token «для
проверки config». Секреты, права и минимальная открытая поверхность — предмет 6.5.

### 7. Подключи к одному host

Выбери один MCP-compatible host, который у тебя уже есть, и зафиксируй его название и
версию. Добавь STDIO entry, полностью перезапусти host, затем:

1. открой список доступных MCP capabilities;
2. убедись, что видишь то же public name, что в Inspector;
3. вызови тот же известный успешный сценарий;
4. сравни arguments и предметный result с Inspector;
5. найди, где host показывает MCP status и logs.

Если модель сама выбирает инструменты, сформулируй проверяемый запрос:

```text
Используй get_release_decision для run_id phase-5-paid-revenue-q2.
До вызова назови выбранный tool и arguments, после — покажи structured result.
Не используй другие tools.
```

Не оценивай подключение по красивому тексту модели. Доказательство — host действительно
зарегистрировал нужную capability, выполнил tool call и получил тот же domain result.

### 8. Воспроизведи один контролируемый сбой

Сначала сохрани рабочий config. Затем измени **ровно одну** деталь: в копии STDIO entry
замени путь к `release_decision_server.py` на несуществующий `missing_server.py`.
Полностью перезапусти host и зафиксируй:

- исчезла ли capability или появился connection error;
- появился ли server process;
- какую точную причину показывает host log;
- на какой ступени диагностической лестницы остановился прогон.

Ожидаемый диагноз: in-memory tests и Inspector до изменения были зелёными, но host не
смог запустить указанный target; значит, наблюдаемый дефект находится в host config /
process startup, а не в tool schema или domain logic.

Верни правильный путь, снова полностью перезапусти host и повтори успешный вызов. Урок
не завершён, если после эксперимента config оставлен сломанным.

Другие сбои исследуй только при реальной необходимости:

| Симптом | Первая проверка | Вероятный слой |
|---|---|---|
| Inspector не запускает process | command, absolute path, dependency, cwd | process/config |
| В STDIO log есть invalid JSON | случайный вывод в `stdout`; перенеси logs в `stderr` | transport/framing |
| Capability видна, но input отклонён | required fields и types в descriptor | public contract |
| Inspector работает, host не видит server | config, полный restart, host support/policy | host integration |
| Один и тот же вызов даёт domain error везде | input и безопасный data adapter | application/domain |
| HTTP endpoint недоступен | запущен ли server, URL, port, network policy | process/network transport |

## Как использовать ИИ при подключении: 4D

ИИ полезен для черновика config и списка гипотез, но подключение нельзя принять по его
уверенному сообщению.

- **Delegation:** делегируй перевод уже проверенных `command` и `args` в формат выбранного host или первичную классификацию конкретного log excerpt.
- **Description:** передай OS, host и его версию, SDK `>=2,<3`, выбранный transport, абсолютный target, один симптом и один обезличенный фрагмент log. Не отправляй весь config с secrets.
- **Discernment:** требуй связать каждую гипотезу с наблюдением и ступенью лестницы. Совет «переустановить всё» без локализации не считается диагнозом.
- **Diligence:** меняй одну переменную, сохраняй команду и результат, возвращай baseline и повторяй тот же capability call после исправления.

## SHIP IT — connection and diagnostics record

Скопируй и заполни
[`outputs/connection-and-diagnostics-record.md`](../outputs/connection-and-diagnostics-record.md).
Положи его рядом с личным server, не копируя исходники ещё раз:

```text
6.3-mcp-server/
├── pyproject.toml
├── uv.lock
├── code/
│   ├── <your_server>.py
│   └── test_<your_server>.py
├── mcp-server-build-record.md
└── connection-and-diagnostics-record.md
```

Артефакт должен позволять другому человеку повторить подключение без догадок, но не
должен раскрывать tokens, credentials, персональные данные или полный чувствительный
config.

## Что этот урок доказал — и чего не доказал

После завершения можно утверждать:

- server остаётся зелёным in-memory;
- отдельный process запускается выбранной командой;
- выбранная capability обнаруживается и вызывается через Inspector;
- тот же server подключён к одному конкретному host;
- один сбой воспроизведён, локализован и исправлен по свидетельствам.

Пока нельзя утверждать:

- что проверены все paths бизнес-логики;
- что server совместим с любым host и transport;
- что подключение безопасно для рабочих данных;
- что права минимальны, identity проверена, а опасные действия требуют approval;
- что server готов к удалённому production deployment.

Первый пункт остаётся за behavioural tests и доменными evals. Безопасность, доступ и
открытая поверхность переходят в 6.5.

## ЧАСТЫЕ ОШИБКИ

- **Писать собственный мини-инспектор.** Он обычно проверяет придуманный `handle()` и обходит настоящий process, transport и host config — главные риски этого урока.
- **Вручную реализовывать legacy `initialize`.** Основной маршрут курса использует `MCPServer` SDK 2.x и [текущую stateless-модель](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports); negotiation и backward compatibility оставь SDK и Inspector.
- **Считать Inspector тестом бизнес-логики.** Он позволяет наблюдать реальные calls, но полноту предметного поведения доказывают tests 6.3.
- **Запускать Inspector на чужом `node build/index.js`.** Target урока — Python server, который студент собрал в 6.3.
- **Использовать относительные пути в host config.** Host может стартовать с другой cwd и не найти ни `uv`, ни server.
- **Печатать отладку в STDIO `stdout`.** Этот канал занят MCP messages; logs отправляй в `stderr`.
- **Менять сразу code, config и transport.** После такого эксперимента исчезает причинная связь между изменением и результатом.
- **Объявлять успех по ответу модели.** Проверь фактический tool call, arguments, result и host logs.
- **Вставлять секрет в screenshot или record.** Для reference-server он не нужен; в личном случае сохрани только redacted evidence.
- **Считать зелёный Inspector гарантией безопасности.** Это отдельная проверка 6.5.

## ЧТО СОЗНАТЕЛЬНО НЕ ВХОДИТ В УРОК

- второй учебный MCP-server и повторная реализация capability;
- самописный protocol/conformance inspector;
- обязательный прогон STDIO и Streamable HTTP одновременно;
- настройка всех популярных hosts;
- OAuth, authentication, approvals и least privilege;
- production deployment, public endpoint и сетевой observability stack;
- полная матрица backward compatibility со старыми MCP revisions.

## ПРОВЕРЬ СЕБЯ

Вопросы ниже проверяют локализацию по слоям, границу доказательства Inspector, правила
STDIO и воспроизводимое подключение к host.

{{quiz}}

## Дополнительное чтение

- [MCP — Inspector](https://modelcontextprotocol.io/docs/tools/inspector) — визуальный тест-инструмент.
- [modelcontextprotocol/inspector](https://github.com/modelcontextprotocol/inspector) — исходники и CLI-режим.
- [MCP — Build an MCP server](https://modelcontextprotocol.io/docs/develop/build-server) — установка сервера в Claude Desktop.
- [Claude Code — Connect via MCP](https://code.claude.com/docs/en/mcp) — подключение MCP-сервера к Claude Code (STDIO/HTTP, scopes).
- [Cursor — Model Context Protocol](https://cursor.com/docs/mcp) — подключение сервера к Cursor через `mcp.json` (STDIO и Streamable HTTP).
- [Integrating MCP with Cursor: A Comprehensive Guide (Medium)](https://medium.com/@UshioShizuku/integrating-model-context-protocol-mcp-with-cursor-a-comprehensive-guide-a3396e65c66b) — практическая настройка и подводные камни.
- [MCP Inspector: Test and Debug your MCP Server Locally (YouTube)](https://www.youtube.com/watch?v=Y0tZ35dFFx4) — видео-прогон тестирования сервера через Inspector.

---
**Часы:** ~3 · **DoD:** server из 6.3 остаётся зелёным in-memory; его отдельный process
исследован через официальный Inspector по выбранному transport; descriptor, успех и
отказ зафиксированы; та же capability вызвана из одного конкретного host; один
контролируемый сбой локализован, исправлен и описан в redacted connection record. ✅
**Урок готов**
