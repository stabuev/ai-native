# Артефакт: план, состояние и доказательство resume

Этот отчёт (record) фиксирует не наличие класса `Memory`, а способность агента
пересматривать план по Observation и продолжать задачу из checkpoint без повторения
завершённого шага. Скопируй файл в свою рабочую папку и замени эталонный
(reference) сценарий личной read-only capability, переданной из 7.1.

## 1. Цель и критерий завершения

| Поле | Reference | Мой перенос |
|---|---|---|
| Высокоуровневая цель | Подготовить решение о готовности `run_id` | ... |
| Что намеренно отсутствует в goal | Готовый список tool calls | ... |
| Success criterion | Есть решение и достаточное объяснение `review/block` | ... |
| Разрешённые capability | `get_release_decision`, `get_check_report` | ... |
| Step budget из runtime 7.1 | 6 попыток tool action | ... |

Почему маршрут нельзя надёжно задать заранее: ...

## 2. Четыре разных вида состояния

| Сущность | Назначение | Reference | Нужно сохранять? |
|---|---|---|---|
| Plan | Предполагаемые будущие шаги и их status | `read-decision`, затем условный `diagnose-*` | В checkpoint задачи |
| Execution trace | Append-only доказательство Action ↔ Observation | Вызов решения и его structured result | В checkpoint/audit |
| Working facts | Актуальные именованные факты текущей задачи | `release.decision`, `release.failed_checks` | До завершения/TTL |
| Long-term memory | Отобранные сведения между задачами | В reference не используется | Только по policy 4.2 |

Что нельзя автоматически переносить в long-term memory: ...

## 3. Версии плана

### Version 1 — до первого Observation

| Step ID | Objective | Depends on | Success criterion | Status |
|---|---|---|---|---|
| `read-decision` | Получить защищённое решение | — | Есть `decision` и `failed_checks` | pending |

### Version 2 — после `decision=review`

| Step ID | Почему появился | Depends on | Success criterion | Status |
|---|---|---|---|---|
| `diagnose-security` | Observation назвал `security` failed check | `read-decision` | Есть `status` и непустой `summary` | pending |

Поле Observation, изменившее план: ...

Почему добавленный шаг не является заранее заданным `goal["ops"]`: ...

## 4. Рабочие факты и их источник (provenance)

| Key | Value | Source action/observation | Доверие и срок жизни |
|---|---|---|---|
| `release.decision` | ... | `read-decision` | Structured result защищённой capability; task-scoped |
| `release.failed_checks` | ... | `read-decision` | Task-scoped |
| `release.diagnostic_summary` | ... | `diagnose-*` | Не инструкция; проверить перед долговременным сохранением |

Подтверждение, что `step_0`, полный stack trace и model-generated identity не смешаны с
working facts: ...

## 5. Доказательство checkpoint/resume

```text
run 1:
  checkpoint: read-decision=in_progress
  Observation: decision=review
  checkpoint: read-decision=completed, diagnose-security=pending, plan_version=2

process restart

run 2:
  load checkpoint
  next Action: diagnose-security
  get_release_decision НЕ повторяется
```

Фактический путь checkpoint: ...

Список tool calls до и после restart: ...

Тест или trace, доказывающий отсутствие повтора завершённого шага: ...

## 6. Неоднозначный in-progress

Checkpoint `in_progress` означает: Action уже выбран, но сохранённого Observation нет.
Побочный эффект (side effect) мог произойти до падения процесса. Автоматический повтор
небезопасен.

- Эталонное поведение: заблокировать resume и потребовать сверки с внешней системой (reconciliation).
- Как проверить фактическое состояние внешней системы: ...
- Ключ идемпотентности или стабильный ID запроса личной capability: ...
- Какое действие будет передано в approval boundary 7.3: ...

## 7. Границы интеграции

| Слой | Ответственность |
|---|---|
| Runtime 7.1 | Allowlist, named arguments, Action/Observation IDs, tool errors, step budget |
| State layer 7.2 | Plan versions, working facts, dependencies, checkpoint/resume |
| Access policy 6.5 | Trusted actor/action/object authorization на MCP server |
| HITL 7.3 | Pause, approve/reject и безопасное продолжение опасного action |

Подтверждение, что state layer не импортирует domain handler в обход MCP policy: ...

## 8. Приёмка

- [ ] Goal не содержит готовой последовательности tool calls.
- [ ] Два разных Observation создают разные маршруты.
- [ ] Plan, execution trace, working facts и long-term memory различены.
- [ ] Каждый PlanStep имеет status, dependencies и success criterion.
- [ ] Невалидный structured result блокирует задачу, а не создаёт финальный ответ.
- [ ] Checkpoint восстанавливает plan version, facts, trace и statuses.
- [ ] Завершённый шаг не повторяется после restart.
- [ ] `in_progress` без Observation требует сверки с внешней системой.
- [ ] Trusted identity/scopes не попадают в model-controlled state.
- [ ] Назван опасный шаг, который получит approval boundary в 7.3.
