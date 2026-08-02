# Урок 6.5 · Контроль доступа для своего MCP-сервера

**Фаза 6 — Инструменты и протоколы (MCP)** · **Результат фазы:** объяснить tool use
изнутри и поднять собственный MCP-сервер с контролем доступа.
<!-- exercise -->

**Результат урока:** после урока ты сможешь взять открытую поверхность своего server из
connection record 6.4, определить доверенную границу и минимальную policy, встроить
проверку action + object до domain adapter, доказать разрешённый и запрещённый вызовы и
зафиксировать остаточные риски без заявления «server теперь безопасен вообще».

**Роль в маршруте:** обязательный финал Фазы 6. Server из 6.3 уже работает, а 6.4
доказал его реальное подключение. Теперь нужно ограничить то, что этот server позволит
будущему агенту Фазы 7.

**Опоры:** public contract и validation из 6.1; trust boundaries и transport layers из
6.2; личный `MCPServer` и behavioural tests из 6.3; выбранный transport, host и раздел
`Handoff в 6.5` из `connection-and-diagnostics-record.md` урока 6.4.

**Requires:** существующий проект `6.3-mcp-server`, Python 3.10+, `uv`,
`mcp>=2,<3` и `pytest`. Reference-практика использует локальный STDIO-сценарий,
синтетические данные и работает без API-ключа, OAuth server и рабочей БД. Сеть нужна
только при первой установке зависимостей.

> **MOTTO.** Модель предлагает arguments. Доверенный context задаёт server. Policy
> решает, пересекут ли arguments доменную границу.

## Новая проблема после успешного подключения

В 6.4 Inspector и выбранный host увидели capability и получили ожидаемый результат.
Для reference-server это означает, что вызов
`get_release_decision(run_id)` действительно доходит до отдельного process и читает
решение quality gate.

Представь, что в безопасной fixture есть две записи:

```text
phase-5-paid-revenue-q2  → publish
phase-5-orders-anomaly   → review
```

Локальному deployment разрешено показывать только первую. Модель передаёт вторую:

```json
{"run_id": "phase-5-orders-anomaly"}
```

Запрос корректен по schema: `run_id` — строка, обязательное поле присутствует. Но
корректная форма ещё не означает право читать этот объект. Если handler сразу вызовет
domain lookup, данные пересекут границу до решения о доступе.

Поэтому server должен ответить на другой вопрос **до** обращения к fixture, файлу или
БД:

> Разрешены ли этому проверенному caller/context именно это действие и именно этот
> объект?

Причина tool call не меняет правило. Модель могла неверно выбрать инструмент, получить
неоднозначную инструкцию или прочитать недоверенный текст. Подробно prompt injection
будет разобран в Фазе 11; здесь достаточно инженерного инварианта: **tool arguments —
недоверенный input, а не доказательство полномочий**.

## Пять разных проверок, которые нельзя смешивать

Сначала раскроем термины обычным языком:

| Проверка | На какой вопрос отвечает | Пример |
|---|---|---|
| Authentication | Кто вызывает server и на основании какого проверенного свидетельства? | локальный process запущен конкретным host/OS user; HTTP token проверен middleware |
| Authorization | Что этому actor/context разрешено сделать и над какими объектами? | `release_decision:read` только для одного `run_id` |
| Validation | Имеют ли arguments допустимую форму и значения? | `run_id` обязателен и имеет тип string |
| Approval | Нужно ли человеку подтвердить этот конкретный высокорисковый вызов? | publish, delete или внешняя отправка ждёт approve |
| Audit | Как потом восстановить принятое решение? | actor, capability, object reference, allow/deny и reason code |

**Actor** — тот, от чьего имени выполняется запрос. **Trusted context** — данные об actor
и его permissions, полученные не из tool arguments, а из доверенной границы deployment.
**Policy** — правило, сопоставляющее context, действие и объект с решением allow/deny.

Эти проверки дополняют друг друга:

- schema-valid запрос может быть запрещён policy;
- разрешённое действие может требовать human approval;
- правильный token не даёт автоматически доступ ко всем объектам;
- audit объясняет решение, но не предотвращает его сам;
- read-only уменьшает риск изменения, но чтение всё ещё может раскрыть секретные данные.

В этом уроке мы реализуем **authorization policy** для одной реальной capability и
наблюдаемый audit decision. Authentication source выбирается по transport, а полноценный
approval workflow остаётся 7.3.

## Главная граница: context не приходит от модели

Небезопасный public contract выглядел бы так:

```python
@mcp.tool()
def get_release_decision(run_id: str, actor: str, scopes: list[str]):
    ...
```

Тогда caller может просто попросить:

```json
{
  "run_id": "phase-5-orders-anomaly",
  "actor": "admin",
  "scopes": ["*"]
}
```

Строка `"admin"` не доказывает личность, а `"*"` не доказывает выданное право. Это
самодекларация недоверенного input.

Правильный поток разделяет два канала:

```text
trusted deployment boundary ──► AccessContext(actor, scopes, object bounds)
                                      │
model/tool arguments ──► SDK schema ──┼─► policy ── allow ──► domain adapter
                                      │
                                      └─► deny + safe audit event
```

Модель видит и заполняет только предметный `run_id`. `actor`, `scopes` и границы
объектов находятся на стороне server. Даже если client пришлёт лишние поля с такими
именами, они не заменяют `AccessContext`, который handler получает из trusted source.

## Откуда берётся trusted context

Transport меняет источник доверия. Один рецепт нельзя механически применить и к STDIO,
и к удалённому HTTP.

### Локальный STDIO

В основном маршруте курса host запускает server как дочерний process. Здесь важны:

- точная команда запуска и осознанное согласие пользователя на неё;
- OS account и permissions, с которыми работает process;
- минимальный доступ process к файлам, сети и внешним credentials;
- server-owned startup configuration с разрешённой surface;
- STDIO вместо оставленного без защиты localhost-порта, когда сеть не нужна.

Reference `LOCAL_ACCESS` — не OAuth identity и не доказательство нескольких пользователей.
Это явная deployment policy одного локального process: что разрешено текущей установке.
Модель не может расширить её через arguments.

Фраза «секрет пришёл через environment» тоже не означает authentication caller. Env
может безопаснее кода передать server credential к внешнему API, но доступ process к
этому credential всё равно нужно минимизировать.

### Удалённый HTTP

Для HTTP-based transport MCP определяет отдельный authorization flow. Protected server
проверяет access token, предназначенный именно ему, и извлекает trusted identity/scopes
до вызова handler. Token нельзя принимать для чужого audience или без проверки
пересылать downstream API.

В этом уроке OAuth не реализуется вручную. Для настоящего HTTP deployment используй
проверенный auth provider/middleware и отобрази его validated context в тот же
application-level `AccessContext`. Точное требование задаёт
[MCP Authorization 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization).

## Reference policy: action + object, а не имя в глобальном списке

В 6.3 reference-server публиковал одну read-only capability. В защищённой версии у неё
есть собственное требование:

```python
READ_RELEASE_SCOPE = "release_decision:read"
```

`AccessContext` хранит server-owned policy:

```python
@dataclass(frozen=True)
class AccessContext:
    actor: str
    scopes: frozenset[str]
    allowed_run_ids: frozenset[str]
```

Reference deployment разрешает действие чтения и только один объект:

```python
DEFAULT_LOCAL_ACCESS = AccessContext(
    actor="local-course-operator",
    scopes=frozenset({"release_decision:read"}),
    allowed_run_ids=frozenset({"phase-5-paid-revenue-q2"}),
)
```

Почему нужны обе проверки:

| Context / request | Scope | Object bound | Решение |
|---|---:|---:|---|
| read permission + разрешённый `run_id` | да | да | allow → domain lookup |
| нет read permission + разрешённый `run_id` | нет | да | deny до lookup |
| read permission + существующий, но чужой `run_id` | да | нет | deny до lookup |

Глобальное множество вроде `WRITE_TOOLS = {"delete_file", ...}` хрупко: новый mutating
tool легко забыть добавить. Ещё опаснее API `guarded_call(tool_name, arbitrary_fn)`: имя
`read_file` может пройти policy, а фактически переданная функция выполнить удаление.

В reference-решении такой пары «доверенное имя + несвязанная функция» нет. Policy
вызвана **внутри конкретной public capability**, а затем следует конкретный domain
adapter:

```python
def get_release_decision(run_id: str) -> ReleaseDecision:
    require_release_access(LOCAL_ACCESS, run_id)
    return lookup_release_decision(run_id)
```

Порядок — часть security contract. Тесты подменяют lookup функцией, которая немедленно
падает. Если deny-тест остаётся зелёным, запрещённый запрос действительно не пересёк
domain boundary.

## Safe denial и audit — разные поверхности

Caller получает одно и то же ограниченное сообщение для отсутствующего permission и
объекта вне policy:

```text
Access denied by server policy.
```

Это не раскрывает список доступных scopes, существование чужого объекта или внутренний
путь. В защищённый audit пишется более точный reason code:

```json
{
  "actor": "local-course-operator",
  "capability": "get_release_decision",
  "object_ref": "phase-5-orders-anomaly",
  "allowed": false,
  "reason_code": "object_out_of_scope"
}
```

Reference использует in-memory list только для наблюдаемой практики. Production audit
должен идти в защищённый structured logger и обычно дополняться server-generated
timestamp и correlation ID. Не записывай access token, secret, полный документ, тело
письма или все arguments «на всякий случай».

Важно: `allowed: true` означает **решение policy**, а не успешное выполнение handler.
Domain adapter может упасть позже; execution outcome и access decision не следует
сливать в одно поле.

## BUILD IT — защити capability из 6.3

### 1. Верни baseline и сделай прогноз

Работай в том же личном проекте, который прошёл 6.3–6.4:

```bash
cd ai-native-work/course-work/phase-6/6.3-mcp-server
uv run pytest code -q
```

До изменения ответь письменно:

1. Дойдёт ли вызов до domain adapter, если schema корректна, но permission отсутствует?
2. Может ли поле `actor="admin"` в tool arguments изменить trusted context?
3. Достаточно ли read-only annotation, чтобы скрыть чувствительный объект?

Правильные ответы будут доказаны тестами: **нет, нет, нет**.

Если используешь Git, зафиксируй зелёный baseline отдельным commit. Если нет — сохрани
копию текущего server вне исполняемого `code/`, чтобы можно было сравнить изменения, но
не оставляй два почти одинаковых production targets в host config.

### 2. Прогони reference-механику

Со страницы урока скопируй в `code/`:

- `secured_release_decision_server.py` — защищённое продолжение reference-server 6.3;
- `test_secured_release_decision_server.py` — behavioural specification доступа.

Запусти:

```bash
uv run pytest code/test_secured_release_decision_server.py -q
uv run python code/secured_release_decision_server.py
```

**Готово, когда пять тестов зелёные:**

1. public schema содержит только domain input и не публикует identity/permissions;
2. разрешённые action + object возвращают прежний structured result;
3. отсутствующий scope даёт tool error до domain lookup;
4. существующий, но out-of-scope object даёт тот же safe denial до lookup;
5. присланные client поля `actor/scopes` не заменяют trusted context server.

Эталон специально не реализует filesystem path sandbox, OAuth server или универсальный
RBAC framework. Он делает наблюдаемым центральный security invariant на уже знакомой
capability.

### 3. Перенеси policy на свой server

Reference доказывает механизм, но не завершает урок. Открой раздел `Handoff в 6.5`
своего connection record и сделай следующее:

1. Назови одну реальную capability, одно действие и один объект или класс объектов.
2. Определи trusted source context для выбранного transport.
3. Удали `actor`, `role`, `tenant`, `scope` из public arguments, если caller мог назначить их себе сам.
4. Задай capability-specific permission: например, `report:read`, `dataset:query` или `release_decision:read`.
5. Добавь object bound: project ID, dataset allowlist, безопасный root/adapter или tenant binding.
6. Вызови policy до чтения, записи, сети или другого domain side effect.
7. Верни caller ограниченный denial, а в audit запиши безопасный reason code.
8. Перепиши reference-tests под свою capability и добейся red → green.

Не переносись механически на `allowed_run_ids`, если твоя граница другая:

| Primitive / действие | Action permission | Object boundary |
|---|---|---|
| tool читает отчёт | `report:read` | project/report IDs, доступные deployment |
| tool выполняет SQL | `dataset:query` | allowlist datasets + только разрешённый query shape |
| resource отдаёт документ | `document:read` | owner/tenant binding или безопасный corpus |
| tool создаёт черновик письма | `email:draft` | разрешённые recipients/domains; отправка отдельно |
| tool изменяет состояние | capability-specific write permission | конкретный объект + отдельная отметка `approval_required` для 7.3 |

Filesystem path — только один возможный object boundary. Если он действительно нужен,
используй platform-aware path resolution, проверяй итоговый canonical target внутри
разрешённого root, учитывай symbolic links и дополнительно ограничивай process на уровне
ОС/sandbox. Проверка строки на `..` сама по себе недостаточна.

### 4. Докажи deny на реальном transport

После in-memory tests снова открой **личный** target через Inspector:

```bash
uv run mcp dev code/<your_server>.py
```

Повтори два сценария:

- разрешённые action + object дают прежний ожидаемый result;
- запрещённый object или отсутствующий permission дают safe denial и audit event, а чувствительные данные не появляются в response.

Если имя target изменилось, обнови STDIO command выбранного host, полностью перезапусти
его и повтори тот же allow/deny. Не объявляй policy рабочей только по прямому вызову
Python-функции: нужно сохранить descriptor, MCP result envelope и реальный transport.

## Самостоятельное решение: матрица доступа

Минимальная policy — это не класс `Principal`, а принятое решение. Для своей capability
заполни хотя бы две строки:

| Trusted actor/context | Action | Object bound | Outcome | Почему |
|---|---|---|---|---|
| ... | ... | ... | allow | ... |
| ... | ... | ... | deny / approval required | ... |

Сильная строка содержит предметную границу: «локальный deployment аналитика может
читать только решения project A». Слабая строка повторяет код: «reader может read».

Если действие изменяет состояние или имеет дорогой внешний эффект, одной authorization
может быть мало. Отметь `approval_required`, но не пиши собственный диалог подтверждения
в этом уроке: пауза, approve/reject и восстановление agent state — результат 7.3.

## Как использовать ИИ: 4D для security-sensitive правки

- **Delegation:** отдай ИИ черновик policy helper, негативных tests или матрицы, но не решение о trusted identity и допустимых объектах.
- **Description:** передай connection record 6.4, transport, фактическую capability, asset, action/object bounds, ожидаемые allow/deny и запрет на secrets и новые production integrations.
- **Discernment:** ищи обход, а не только happy path: может ли caller назначить себе role, разрешает ли label вызвать несвязанную функцию, попадает ли deny в adapter, раскрывает ли error чужой объект.
- **Diligence:** прочитай diff, запусти все tests, повтори deny через Inspector/host, проверь audit и поиском убедись, что tokens и credentials не попали в code, schemas, responses или record.

ИИ не подтверждает безопасность фразой «реализован RBAC». Доказательство — конкретная
policy, независимый denied path до side effect и явно названные остаточные риски.

## SHIP IT — access-control record и досье Фазы 6

Скопируй и заполни два артефакта:

- [`outputs/mcp-access-control-record.md`](../outputs/mcp-access-control-record.md) — доказательства policy и остаточные риски конкретного server;
- [`outputs/phase-6-dossier.md`](../outputs/phase-6-dossier.md) — сквозная приёмка одной capability от 6.1 до handoff в Фазу 7.

Access-control record положи рядом с build record 6.3 и connection record 6.4:

```text
6.3-mcp-server/
├── pyproject.toml
├── uv.lock
├── code/
│   ├── <your_server>.py
│   └── test_<your_server>.py
├── mcp-server-build-record.md
├── connection-and-diagnostics-record.md
└── mcp-access-control-record.md
```

Досье фазы хранится уровнем выше:

```text
course-work/phase-6/
├── 6.1-tool-use/...
├── 6.2-mcp-architecture/...
├── 6.3-mcp-server/...
└── phase-6-dossier.md
```

Артефакт фиксирует не обещание «secure», а доказанную policy для конкретной surface,
transport-specific trust source, allow/deny evidence и остаточные риски. Он передаёт в
Фазу 7 инструменты, которыми агент может пользоваться сразу, и действия, где ему нужен
human approval.

## Как этим уроком закрывается Фаза 6

Досье должно показать один непрерывный переход, а не пять независимых домашних работ:

```text
6.1 public contract + success/rejection trace
  → 6.2 host/client/server boundary + primitive + compatibility failure
  → 6.3 generated descriptor + in-memory behavioural evidence
  → 6.4 process/transport + Inspector + один host + восстановленный config failure
  → 6.5 trusted context + action/object policy + allow/deny + residual risks
```

Предметная задача, capability и ожидаемый успешный результат должны узнаваться на каждом
шаге. Если контракт менялся, укажи точную причину и повторённые проверки. В досье не
нужно вставлять все logs и исходники: дай короткие evidence и ссылки на заполненные
records.

Для 7.1 передай одну уже разрешённую read-only capability, её domain arguments и
ожидаемую observation. Agent loop должен вызывать её через MCP adapter, а не импортировать
domain handler в обход server policy. Для 7.3 передай только конкретное дорогое,
необратимое или внешнее действие, которому после authorization действительно нужен
human approval. Если такого действия у server нет, честно запиши «не требуется», а не
добавляй опасный tool ради шаблона.

## Что теперь доказано — и чего нет

После завершения можно утверждать:

- trusted context не выбирается моделью через public arguments;
- одна реальная capability проверяет action + object до domain adapter;
- разрешённый путь сохраняет предметное поведение 6.3–6.4;
- два реалистичных deny-path наблюдаемы через MCP client;
- audit отличает policy decision и не раскрывает secrets;
- опасные действия, требующие approval, переданы в 7.3.

Пока нельзя утверждать:

- что самостоятельно реализован корректный OAuth authorization server;
- что local process изолирован от всей файловой системы и сети;
- что проверены все capabilities, tenants и object relationships;
- что policy защищает от всех видов prompt injection и tool poisoning;
- что audit storage защищён от подмены и имеет production retention;
- что server прошёл профессиональный security review или penetration test.

## ЧАСТЫЕ ОШИБКИ

- **Брать actor или scopes из tool arguments.** Это недоверенная самодекларация caller, а не authentication.
- **Проверять только имя tool.** Policy должна быть привязана к конкретному handler и проверять action + object до side effect.
- **Считать read-only безопасным автоматически.** Чтение может раскрыть чужой отчёт, персональные данные или secret.
- **Путать schema validation и authorization.** Корректный `run_id: str` всё ещё может быть вне разрешённой surface.
- **Проверять policy после lookup или write.** Deny после side effect ничего не защищает.
- **Возвращать подробный denial caller.** Список scopes, существование объекта и внутренние пути нужны защищённому audit, а не модели.
- **Логировать полный input/output и tokens.** Audit сам становится источником утечки.
- **Применять HTTP OAuth recipe к локальному STDIO.** Для STDIO важны command consent, OS/process permissions, sandbox и минимальная startup policy.
- **Принимать token для чужого audience или пересылать его downstream.** Remote server должен валидировать token для собственного resource и не использовать token passthrough.
- **Считать authorization заменой approval.** Разрешённое policy высокорисковое действие может всё равно требовать решения человека в 7.3.

## ЧТО СОЗНАТЕЛЬНО НЕ ВХОДИТ В УРОК

- самостоятельная реализация OAuth/OIDC server, JWT parser и token validation;
- универсальный RBAC/ABAC framework для всех предметных областей;
- полноценный filesystem sandbox, container profile и network policy;
- human approval workflow и pause/resume agent state — 7.3;
- глубокая защита от prompt injection, tool poisoning и data exfiltration — Фаза 11;
- production SIEM, retention policy, incident response и penetration testing;
- утверждение о полной безопасности server после одного упражнения.

## ПРОВЕРЬ СЕБЯ

Вопросы ниже проверяют trust source, различие validation/authorization/approval,
action-object policy, transport-specific access и безопасный audit.

{{quiz}}

## Дополнительное чтение

Это факультативная библиотека, а не продолжение обязательной части урока. Читать всё не требуется: выбери маршрут под свою задачу.

### Если нужен точный контракт MCP

- [MCP — Understanding Authorization](https://modelcontextprotocol.io/docs/tutorials/security/authorization) — начни с разделов **When Should You Use Authorization?** и **Security Considerations**: они объясняют, когда локальному STDIO-серверу достаточно trusted context, а когда удалённому HTTP-серверу нужен OAuth-поток.
- [MCP — Authorization specification](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization) — обращайся к разделам **Purpose and Scope**, **Scope Selection Strategy**, **Token Handling** и **Runtime Insufficient Scope Errors**, когда проектируешь production HTTP-сервер; это нормативный источник, а не вводное чтение.
- [MCP — Security Best Practices](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices) — для продолжения этого урока особенно полезны **State Handle Hijacking**, **Local MCP Server Compromise**, **stdio Transport Security in Proxy Scenarios** и **Scope Minimization**.

### Если нужен практический security review

- [OWASP GenAI — A Practical Guide for Secure MCP Server Development](https://genai.owasp.org/resource/a-practical-guide-for-secure-mcp-server-development/) — используй как внешний чек-лист для архитектуры, authentication/authorization, валидации, изоляции сессий и hardened deployment; сравни его пункты со своим access-control record.
- [Red Hat — MCP: Understanding security risks and controls](https://www.redhat.com/en/blog/model-context-protocol-mcp-understanding-security-risks-and-controls) — короткий независимый обзор confused deputy, least privilege и границ доверия; полезен, если официальный текст пока кажется слишком нормативным.

### Если нужна модель угроз шире access control

- [Simon Willison — The lethal trifecta](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) — проверь, не совмещает ли система приватные данные, недоверенный контент и канал наружу; эта рамка понадобится глубже в фазе про prompt injection.
- [Invariant Labs — MCP Tool Poisoning Attacks](https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks) — показывает, почему опасность может находиться не в аргументах вызова, а в описании инструмента, и зачем контролировать происхождение и изменение MCP-серверов.

### Если хочется hands-on практики

- [Damn Vulnerable MCP Server](https://github.com/harishsg993010/damn-vulnerable-MCP-server) — десять намеренно уязвимых сценариев: выбери один-два после урока и запускай только изолированно, на синтетических данных и без реальных секретов.

---
**Часы:** ~4 · **DoD:** личная capability использует trusted server-side context и
проверяет capability-specific action + object до domain adapter; allow, missing
permission, out-of-scope object и попытка self-assigned context доказаны behavioural
tests; allow/deny повторены через реальный transport; redacted access-control record
фиксирует policy, audit evidence и residual risks; досье связывает evidence 6.1–6.5 и
передаёт безопасную capability в 7.1, а применимое действие с approval — в 7.3. ✅
**Урок готов**
