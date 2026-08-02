# Артефакт 6.2 · Карта MCP-границ и два trace

Скопируй шаблон в личную папку:

```text
ai-native-work/course-work/phase-6/6.2-mcp-architecture/mcp-boundary-and-traces.md
```

Не подключай внешний server ради заполнения. Здесь оценивается архитектурное решение;
реализация, transport и инспекция начнутся в 6.3–6.4.

## 1. Handoff из 6.1

**Артефакт 6.1:** `ai-native-work/course-work/phase-6/6.1-tool-use/tool-contract-and-trace.md`

**Пользовательская задача:** ...

**Public tool name и назначение:** ...

**Domain input/output contract:** ...

**Успешный и отклонённый evidence, который переносим:** ...

**Что остаётся неизменным:** пользовательская потребность, предметный контракт и граница «описание / исполнение» — уточни своё.

**Что меняется в 6.2:** способ discovery, размещение реализации и routing через host/client/server — уточни своё.

**Если capability или primitive нужно изменить — какая конкретная несовместимость это требует:** ...

## 2. Рабочая ситуация

**Какую задачу решает пользователь:**

> ...

**Какой результат он должен увидеть:**

> ...

**Как это делается сейчас и почему локальной интеграции недостаточно:**

> ...

**Какие данные безопасно использовать в учебном trace:**

> ...

## 3. Участники и границы

| Участник | Конкретный компонент | Ответственность | Чего он не делает |
|---|---|---|---|
| Пользователь | ... | ставит задачу, выбирает workflow или подтверждает действие | ... |
| Model | ... | предлагает текст или tool call на основе переданных specs | ... |
| Host | ... | управляет моделью, registry, policies и routing | ... |
| MCP client A | ... | поддерживает target и протокольный обмен с server A | ... |
| MCP server A | ... | публикует и исполняет возможности домена ... | ... |
| MCP client/server B, если нужен | ... | ... | ... |

Проверь количество связей: на каждый server target внутри host должен быть свой MCP
client. Это не делает протокол stateful: в `2026-07-28` каждый request self-contained.

## 4. Доменная граница server

**Название будущего server:** `...`

**Одна связная область ответственности:**

> ...

**Что намеренно остаётся вне server и почему:**

- ...
- ...

**Почему это не “server на все случаи жизни”:**

> ...

## 5. Решения по primitives

Не нужно искусственно использовать все три primitive. Выбери форму, естественную для
сценария, и обоснуй её.

| Возможность | Кто инициирует | Нужная форма результата | Read/write | Primitive | Почему | Почему не альтернативы |
|---|---|---|---|---|---|---|
| ... | model / app / user | ... | ... | tool/resource/prompt | ... | ... |
| ... | ... | ... | ... | ... | ... | ... |
| ... | ... | ... | ... | ... | ... | ... |

### Неоднозначное решение

**Возможность:** `...`

**Два правдоподобных варианта:**

1. ...
2. ...

**Выбор и решающий критерий:**

> Не “потому что это GET/POST”, а кто инициирует использование, является ли результат
> адресуемым контекстом или вычислением и как пользователь должен его обнаружить.

## 6. Compatibility preflight

| Условие | Что требуется сценарию | Как подтвердим | Что делаем при несовместимости |
|---|---|---|---|
| Protocol version | ... | `server/discover` + `_meta` каждого request | ... |
| Server capability | tools/resources/prompts: ... | `server/discover` result | ... |
| Host/client support | ... | документация/настройки host | ... |
| Transport | STDIO или Streamable HTTP: ... | ... | ... |
| Auth/credentials | ... | ... | ... |
| Host policy/approval | ... | ... | ... |
| Content/extension assumptions | ... | ... | ... |

## 7. Успешный end-to-end trace

Заполни конкретными событиями. Не копируй ID из урока: создай собственные и сохрани
явное соответствие.

| Шаг | Откуда → куда | Event / MCP method | Существенный input/output | Correlation ID |
|---:|---|---|---|---|
| 1 | host → client | выбрать server target | server config | — |
| 2 | client → server | `server/discover` | per-request `_meta`: version + client capabilities | MCP request `...` |
| 3 | server → client | discover result | supported versions + server capabilities | MCP response `...` |
| 4 | client ↔ server | `*/list` | `_meta` + descriptor выбранного primitive | MCP request/response `...` |
| 5 | host → model | provider request | user request + normalized specs/context | provider turn `...` |
| 6 | model → host | provider tool call / выбор prompt/resource | ... | provider call `...` |
| 7 | client ↔ server | `tools/call`, `resources/read` или `prompts/get` | `_meta` + params/result | MCP request/response `...` |
| 8 | host → model | переведённый result/context | ... | provider result для call `...` |
| 9 | model → user | финальный ответ | ... | — |

### Карта двух ID

| Provider call ID | MCP JSON-RPC request ID | Как host хранит соответствие |
|---|---|---|
| `...` | `...` | ... |

Если выбран resource или prompt без model tool call, объясни, почему provider call ID на
этом пути отсутствует и какой компонент инициировал получение.

## 8. Failure trace и восстановление

Выбери одно реалистичное нарушение: `server/discover` не объявил нужную capability,
host не поддерживает primitive, request несёт несовместимую version/capabilities, не
прошла auth/policy или routing выбрал неверный server.

**Нарушенное условие:**

> ...

| Шаг | Где обнаружено | Наблюдаемый сигнал | Почему исполнение ещё не произошло |
|---:|---|---|---|
| ... | ... | ... | ... |

**Что увидит пользователь:**

> ...

**Безопасное восстановление или fallback:**

> ...

**Что нельзя делать автоматически:**

> ...

## 9. Handoff в 6.3

**Какой один server реализуем первым:** `...`

**Какая одна capability будет первой:** `...`

**Какие MCP methods потребуются:**

- `server/discover`
- `.../list`
- `.../call`, `.../read` или `.../get`

**Безопасная локальная фикстура для первого прогона:**

> ...

**Что отложено до 6.4 и 6.5:**

> transport/Inspector/подключение; auth/approvals/least privilege/изоляция — уточни своё.

## Рубрика приёмки

- [ ] Пользователь, model, host, MCP clients и servers имеют разные ответственности.
- [ ] Число MCP client targets соответствует числу servers и не подразумевает protocol session state.
- [ ] Каждый primitive выбран по форме взаимодействия и владельцу инициативы.
- [ ] Read-only tool не был ошибочно превращён в resource только из-за отсутствия записи.
- [ ] Успешный trace включает `server/discover`, per-request metadata, listing и использование.
- [ ] В основной ветке нет session state или обязательного `initialize` из старой ревизии.
- [ ] Provider call ID и MCP JSON-RPC request ID не смешаны.
- [ ] Failure trace называет точку отказа и доказывает отсутствие исполнения.
- [ ] Условия совместимости перечислены без обещания “работает в любом host”.
- [ ] Первая capability продолжает 6.1; любое изменение primitive или контракта имеет явную причину.
- [ ] Граница server связная и даёт конкретный первый шаг для 6.3.
- [ ] В артефакте нет секретов, реальных персональных данных и подключения случайного server.
