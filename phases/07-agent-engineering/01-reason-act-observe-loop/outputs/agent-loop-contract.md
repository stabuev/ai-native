# Артефакт: контракт и доказательство agent loop

Этот record фиксирует не обещание «у нас есть агент», а проверяемый контракт одного
reason → act → observe loop. Скопируй файл в свою рабочую папку, замени reference-данные
на личную read-only capability из Фазы 6 и приложи фактические traces.

## 1. Цель и границы

| Поле | Reference | Мой перенос |
|---|---|---|
| Goal | Получить решение по `run_id` и при необходимости объяснить review | ... |
| Разрешённые capability | `get_release_decision`, `get_check_report` | ... |
| Запрещённые действия | Любая запись или публикация релиза | ... |
| Stop condition | Наблюдаемое `final` после достаточного результата | ... |
| Step budget | 6 попыток tool action | ... |
| Остаточный риск | Ошибочное решение policy; устаревший result | ... |

Почему здесь нужен выбор маршрута, а не фиксированный workflow: ...

## 2. Контракт runtime

```text
decision_policy(goal, execution_trace)
    -> Action(kind="tool", action_id, tool, arguments)
    -> Observation(action_id, ok, output | error_code)
    -> новый decision_policy(...)

или

decision_policy(...) -> Action(kind="final", answer)
```

Инварианты:

- `arguments` — объект с именованными полями;
- `Observation.action_id == Action.action_id`;
- action IDs не повторяются;
- unknown tool и invalid arguments не достигают callable;
- tool exception превращается в безопасный `error_code`, без сырого exception в trace;
- каждая попытка tool action расходует budget;
- следующий side effect блокируется до исполнения, если budget исчерпан.

## 3. Доказательство выбора маршрута

### Быстрый финал

```text
goal={run_id: run-ready}
decision-1 get_release_decision({run_id: run-ready})
  -> ok {decision: publish, failed_checks: []}
final {decision: publish, summary: all required checks passed}
```

Фактический trace моего переноса: ...

### Ветка после Observation

```text
goal={run_id: run-review}
decision-1 get_release_decision({run_id: run-review})
  -> ok {decision: review, failed_checks: [security]}
report-security get_check_report({run_id: run-review, check: security})
  -> ok {status: failed, summary: dependency scan requires a human review}
final {decision: review, summary: dependency scan requires a human review}
```

Какое поле Observation изменило следующий шаг: `decision=review` и первый элемент
`failed_checks`. Фактическая ветка моего переноса: ...

### Безопасная ошибка и исправление

```text
decision-1 -> ok=false, error_code=tool_error
decision-2 -> ok=true, output={decision: publish, ...}
final
```

Почему retry ограничен и что произойдёт после второй ошибки: ...

## 4. MCP boundary

| Слой | Что получает | Чего не получает |
|---|---|---|
| Model-backed policy | Tool schemas, public arguments, safe observations | Trusted identity, scopes, server callable |
| Agent runtime | Action, allowlist tools, budget | Право отменять server policy |
| MCP client adapter | Public arguments + trusted context приложения | Самоназначенные моделью роли |
| MCP server | Trusted context, action, object boundary | Доверие к одному имени capability без policy |

Личная capability из `phase-6-dossier.md`: ...

- Public arguments: ...
- Trusted context source: ...
- Capability-specific permission: ...
- Object boundary: ...
- Allow через реальный transport: ...
- Deny через реальный transport: ...
- Подтверждение, что agent loop не импортирует domain handler: ...

## 5. Приёмка

- [ ] Reference-тесты проходят.
- [ ] Два разных Observation приводят к разным маршрутам.
- [ ] Invalid tool/arguments не дают side effect.
- [ ] Tool failure виден как безопасный Observation, policy ограниченно исправляется.
- [ ] После исчерпания budget следующий tool не вызывается.
- [ ] Action и Observation коррелируются по ID.
- [ ] Личная read-only capability вызывается через MCP adapter.
- [ ] Trusted identity/scopes не появляются в model-controlled arguments или trace.
- [ ] Реальные allow и deny из 6.5 повторены после подключения agent loop.

## 6. Handoff в 7.2

Execution trace хранит события текущего запуска, но не решает две задачи длинного
агента:

- **план:** как представить и пересматривать несколько подцелей;
- **память:** какое именованное состояние нужно сохранять и как долго оно живёт.

Что из этого запуска потребуется следующему уроку: ...

Что не следует сохранять в память из-за чувствительности или недоверенного источника: ...
