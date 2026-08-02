# Артефакт 6.5 · MCP access-control and residual-risk record

Заполни record для **того же личного server**, который прошёл 6.3–6.4. Документ не
сертифицирует полную безопасность: он фиксирует одну фактически реализованную policy,
её доказательства и известные остаточные риски. Скрой tokens, credentials, персональные
данные, чувствительные paths и полные рабочие arguments.

## 1. Handoff из 6.4

**Server и target:** ...

**Transport:** STDIO / Streamable HTTP

**Проверенный host:** ...

**Public capability и primitive:** ...

**Какие данные или действия открыты:** ...

**Самый опасный допустимый вызов:** ...

**Какой access gap был выбран первым:** ...

## 2. Доверенная граница

**Asset, который защищаем:** ...

**Trusted actor/context:** ...

**На каком проверенном основании context считается доверенным:** OS/process boundary /
server startup configuration / verified HTTP token / другое — ...

**Какие поля контролирует model/client:** ...

**Какие security-поля принципиально отсутствуют в public schema:** actor / principal /
role / tenant / scopes / другое — ...

**Почему caller не может назначить их себе через arguments:** ...

## 3. Матрица policy

| Trusted actor/context | Action | Object bound | Required permission | Outcome | Обоснование |
|---|---|---|---|---|---|
| ... | ... | ... | ... | allow | ... |
| ... | ... | ... | ... | deny | ... |
| ... | ... | ... | ... | approval required | ... |

Удаляй неприменимые строки. `Approval required` нужен только для реального
высокорискового действия и передаётся в 7.3; он не заменяет allow/deny policy.

## 4. Где и как policy исполняется

**Capability-specific permission:** ...

**Object boundary:** allowlist / owner binding / tenant binding / safe adapter /
canonical filesystem root / другое — ...

**Точка вызова policy:** файл и функция — ...

**Domain adapter или side effect после неё:** ...

**Как доказано, что deny происходит до adapter/side effect:** ...

**Что caller получает при deny:** ...

**Что дополнительно остаётся только в protected audit:** ...

## 5. Behavioural evidence

**Команда tests:**

```bash
...
```

### Public contract

**Фактические properties input schema:** ...

**Почему identity/permissions не являются domain arguments:** ...

### Allow

**Trusted context + action + object:** ...

**Наблюдаемый structured result:** ...

**Audit decision:** ...

### Missing permission

**Изменённая часть trusted context:** ...

**Наблюдаемый tool error:** ...

**Доказательство, что adapter не был вызван:** ...

**Internal reason code:** ...

### Out-of-scope object

**Существующий, но запрещённый object:** ...

**Наблюдаемый tool error:** ...

**Какие сведения caller не получил:** ...

**Доказательство, что adapter не был вызван:** ...

### Попытка self-assigned context

**Какие лишние actor/role/scopes прислал client:** ...

**Какой trusted context фактически увидела policy:** ...

**Почему privilege не изменился:** ...

## 6. Проверка через Inspector и host

**Команда Inspector:**

```bash
...
```

**Allow evidence через transport:** ...

**Deny evidence через transport:** ...

**Host config обновлён на защищённый target:** да / target не менялся / неприменимо

**Повторная проверка в host:** ...

## 7. Audit и чувствительные данные

**Поля audit event:** ...

**Server-generated correlation/time fields:** реализованы / оставлены production logger /
не нужны в учебной fixture — объясни: ...

**Что намеренно не логируется:** ...

**Где защищён audit sink:** in-memory только для урока / protected logger / другое — ...

**Как выполнена redaction артефакта:** ...

## 8. Transport-specific controls

### Если основной transport — STDIO

**Кто подтвердил точную startup command:** ...

**OS identity и process permissions:** ...

**Ограничения filesystem/network:** ...

**Какие upstream credentials доступны process и зачем:** ...

### Если основной transport — HTTP

**Authorization provider/middleware:** ...

**Как валидируются issuer/audience/resource и expiry:** ...

**Как verified scopes попадают в application policy:** ...

**Как исключён token passthrough:** ...

Не заполняй HTTP-раздел обещаниями, если HTTP authorization фактически не реализована.
Оставь его в residual risks.

## 9. Residual risks и handoff

### В 7.1 — безопасная capability для agent loop

**Capability, которую агент может вызывать без дополнительного human approval:** ...

**Domain arguments от модели:** ...

**Ожидаемая observation для следующего шага agent loop:** ...

**Как agent adapter вызывает MCP server, не импортируя domain handler напрямую:** ...

**Какая server-side policy остаётся обязательной при любом вызове агента:** ...

### В 7.3 — действия, которым нужен human approval

| Action | Почему authorization недостаточно | Какой approval нужен в 7.3 |
|---|---|---|
| ... | ... | ... |

Если у server нет дорогих, необратимых или внешних действий, запиши `не требуется` и не
добавляй write-tool только ради заполнения строки.

### В Фазу 11

**Какой недоверенный content может попасть модели через server:** ...

**Какая exfiltration surface остаётся:** ...

### Прочие остаточные риски

- ...

## Рубрика приёмки

- [ ] Record продолжает личный server и handoff 6.4, а не новый generic file demo.
- [ ] Authentication source, authorization policy, validation и approval не смешаны.
- [ ] Trusted identity/permissions отсутствуют в model-controlled arguments.
- [ ] Policy проверяет конкретные action + object, а не только имя tool или read/write flag.
- [ ] Deny доказан до domain adapter или side effect независимым test double.
- [ ] Существующий out-of-scope object не раскрывается через подробный error.
- [ ] Allow сохраняет ожидаемое предметное поведение server 6.3–6.4.
- [ ] Allow и deny повторены через выбранный transport.
- [ ] Audit содержит достаточный reason code, но не secrets и полные sensitive payloads.
- [ ] STDIO и HTTP controls описаны только для фактически выбранного transport.
- [ ] Безопасная capability передана в 7.1 без обхода server policy.
- [ ] Human approval и deep prompt-injection defense честно переданы в 7.3 и Фазу 11.
- [ ] Residual risks конкретны; документ не заявляет production security без доказательств.
