# Досье завершения Фазы 6 · От tool call до защищённого MCP-сервера

Скопируй шаблон в личное пространство — репозиторий курса клонировать не требуется:

```text
ai-native-work/course-work/phase-6/phase-6-dossier.md
```

Досье не заменяет артефакты уроков и не требует вставлять весь код или logs. Оно
доказывает, что **одна и та же собственная capability** прошла путь 6.1–6.5 без скрытой
подмены новым demo, а затем получила честный handoff в Agent Engineering.

## 1. Индекс собственных результатов

Укажи фактические пути внутри `ai-native-work`. Если что-то хранится иначе, объясни,
как другому человеку найти результат.

| Урок | Обязательный результат | Фактический путь | Готово |
|---|---|---|---:|
| 6.1 | tool contract + успешный и отклонённый trace | `course-work/phase-6/6.1-tool-use/tool-contract-and-trace.md` | да / нет |
| 6.2 | MCP boundary + два уровня ID + compatibility failure | `course-work/phase-6/6.2-mcp-architecture/mcp-boundary-and-traces.md` | да / нет |
| 6.3 | server, tests, lock-файл и build record | `course-work/phase-6/6.3-mcp-server/...` | да / нет |
| 6.4 | connection and diagnostics record | `course-work/phase-6/6.3-mcp-server/connection-and-diagnostics-record.md` | да / нет |
| 6.5 | access-control and residual-risk record | `course-work/phase-6/6.3-mcp-server/mcp-access-control-record.md` | да / нет |

## 2. Сквозной контракт одной capability

**Пользовательская задача:** ...

**Почему обычного ответа модели недостаточно:** ...

| Координата | Итоговое значение |
|---|---|
| Public capability name | `...` |
| Primitive | tool / resource / prompt |
| Кто инициирует использование | model / application / user |
| Domain input | ... |
| Structured output / content | ... |
| Server boundary | ... |
| Безопасный data adapter / fixture | ... |
| Transport | STDIO / Streamable HTTP |
| Проверенный host | ... |
| Trusted context source | ... |
| Action permission | ... |
| Object boundary | ... |

**Что сохранилось неизменным от 6.1 до 6.5:** ...

**Что изменилось, почему и какие проверки после этого были повторены:** ...

## 3. Матрица доказательств 6.1–6.5

Ссылайся на короткий фрагмент собственного record, test name, command или redacted log.
Фразы «работает» и «безопасно» без наблюдаемого evidence не считаются доказательством.

| Переход | Что нужно доказать | Evidence | Вывод и его граница |
|---|---|---|---|
| 6.1 | модель видит public spec без callable; invalid call не исполняется | ... | ... |
| 6.2 | роли и primitives не смешаны; provider call ID отделён от MCP request ID | ... | ... |
| 6.3 | SDK публикует ожидаемый descriptor; success и два failure-path наблюдаемы in-memory | ... | ... |
| 6.4 | отдельный process и transport работают; Inspector и один host видят ту же capability | ... | ... |
| 6.4 | одна поломка config локализована, исправлена и перепроверена | ... | ... |
| 6.5 | trusted context не назначается arguments; action + object проверяются до adapter | ... | ... |
| 6.5 | allow сохраняет результат, deny не раскрывает объект, audit хранит reason code | ... | ... |

## 4. Один end-to-end успешный trace

Сократи trace до существенных событий и используй собственные значения:

```text
user request
→ host передал модели public descriptor
→ provider tool call / выбор resource или prompt: ...
→ MCP client request ID: ...
→ server schema validation
→ trusted context + action/object policy: allow
→ domain adapter
→ structured MCP result / content: ...
→ provider result / context
→ финальный ответ пользователю: ...
```

**Как сопоставлены provider call ID и MCP request ID:** ...

**Почему результат пришёл из adapter, а не был заново придуман моделью:** ...

## 5. Отказ, локализация и восстановление

Выбери один уже выполненный controlled failure из 6.4 или deny-path из 6.5. Не ломай
рабочую среду повторно только ради досье.

**Зелёный baseline:** ...

**Одна изменённая координата или запрещённый запрос:** ...

**Предсказанный слой отказа:** contract / process / transport / host / authorization — ...

**Наблюдаемый сигнал:** ...

**Почему domain side effect не произошёл:** ...

**Исправление или безопасный отказ:** ...

**Повторная проверка исходного успеха:** ...

## 6. Граница результата фазы

Теперь доказано:

- [ ] client-side tool-use boundary понятна и проверена;
- [ ] одна собственная capability спроектирована и реализована как MCP primitive;
- [ ] server воспроизводится из lock-файла и проходит behavioural tests;
- [ ] process/transport, Inspector и один конкретный host проверены;
- [ ] одна capability защищена trusted context и action/object policy;
- [ ] allow/deny evidence и redacted audit сохранены.

Пока не доказано:

- совместимость со всеми hosts, transports и protocol revisions;
- безопасность реальной БД, рабочих файлов или production secrets;
- корректность самостоятельно написанного OAuth/OIDC server;
- approval workflow для необратимых действий;
- защита от всех prompt-injection, tool-poisoning и exfiltration сценариев;
- production deployment, observability, incident response и penetration testing.

**Конкретные residual risks моего server:** ...

## 7. Handoff в Agent Engineering

### В 7.1 — reason → act → observe

**Разрешённая capability:** ...

**Какое действие сформирует agent policy:** ...

**Какая observation вернётся в history:** ...

**Как adapter вызывает MCP server, сохраняя server-side policy:** ...

**Что агенту принципиально не передаётся:** callable, trusted identity/scopes, secrets — уточни своё.

### В 7.3 — human-in-the-loop

| Действие | Риск | Почему authorization недостаточно | Условие approval | Что при reject |
|---|---|---|---|---|
| ... / `не требуется` | ... | ... | ... | ... |

### В Фазу 11 — недоверенный контент

**Какие данные server может вернуть модели из внешнего или недоверенного источника:** ...

**Какой канал наружу может превратить это в exfiltration risk:** ...

## 8. Рефлексия

Ответь конкретно по своему server:

1. Какое решение предлагала модель, но не имела права исполнять сама?
2. Что гарантировал MCP-протокол, а что осталось ответственностью host и server?
3. Какая проверка поймала самый правдоподобный дефект?
4. Какой вывод нельзя делать даже после всех зелёных тестов фазы?
5. Какой один следующий шаг в Фазе 7 повышает полезность, не расширяя полномочия?

## Рубрика приёмки

- [ ] Все пять уроков связаны одной пользовательской задачей и узнаваемой capability.
- [ ] Изменения контракта имеют причины и повторные evidence, а не скрыты новым demo.
- [ ] Есть ссылка на фактический success и хотя бы один реалистичный failure/deny.
- [ ] In-memory, Inspector, host и security evidence не выданы за взаимозаменяемые проверки.
- [ ] Досье не содержит secrets, полных чувствительных arguments, персональных данных и неретушированных logs.
- [ ] Результат фазы не обещает production security или универсальную совместимость.
- [ ] Handoff в 7.1 сохраняет server-side policy и не импортирует domain handler напрямую.
- [ ] В 7.3 передано только применимое высокорисковое действие; декоративный write-tool не добавлен.
- [ ] Рефлексия разделяет ответственность модели, host, client, server, policy и человека.
