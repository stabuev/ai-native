# Урок 7.2 · Память и планирование агента

**Фаза 7 — Agent Engineering** · **Результат фазы:** Собрать надёжного агента с памятью, планированием, human-in-the-loop и guardrails.
<!-- exercise -->

**Результат урока:** построить сохраняемое в JSON состояние задачи с планом, номер
версии которого меняется при пересмотре, именованными рабочими фактами и execution
trace; изменить будущий маршрут после нового Observation; сохранить контрольную точку
(checkpoint) и после перезапуска продолжить с первого допустимого шага, не повторив
уже завершённый.

**Опоры:** фиксированная цепочка и динамический выбор маршрута из 2.3; контекст,
история и долговременная память из 4.2; `Action → Observation`, безопасный runtime и
read-only capability из 7.1. BUILD IT работает офлайн, без API-ключа и сети. В
необязательном USE IT ключ понадобится только для model-backed planner.

В 7.1 агент видел execution trace текущего запуска. Этого достаточно, пока процесс не
падает, маршрут короткий, а все нужные результаты легко восстановить из последних
наблюдений. Теперь задача переживёт несколько шагов и перезапуск процесса. Для этого
историю действий нужно дополнить явным состоянием задачи.

Открой свой `agent-loop-contract.md` из 7.1 и найди раздел о передаче в 7.2. В нём уже
есть цель, разрешённые capability, `Action`, `Observation`, trace, stop condition и
step budget. В этом уроке мы не строим второй runtime: мы добавляем над ним слой,
который отвечает на три новых вопроса — что ещё предстоит сделать, какие предметные
факты уже установлены и откуда безопасно продолжить после остановки.

> **Главная мысль.** План — это проверяемая гипотеза о будущих шагах, а не обещание
> выполнить заранее записанный сценарий. Observation меняет факты задачи, факты могут
> изменить план, а checkpoint сохраняет эту границу для безопасного продолжения.

## PROBLEM

Представь задачу «подготовить решение о готовности релиза». Сначала агент читает
решение проверки. Если всё прошло, он может закончить. Если обнаружен сбой безопасности,
нужно запросить диагностическую сводку. До первого результата второй шаг ещё не известен:
это может быть security, quality, permissions или вообще ничего.

Одного списка сообщений здесь недостаточно. После падения процесса приложению нужно
однозначно узнать:

- какой шаг уже завершён и подтверждён Observation;
- какие предметные факты из результата сейчас считаются актуальными;
- какой шаг ожидает выполнения и от чего он зависит;
- менялась ли структура плана;
- не остался ли вызов в опасном состоянии «начали выполнять, но результат не сохранили».

Если вместо этого попросить модель «прочитай историю и продолжи», она будет заново
интерпретировать сообщения. Она может повторить завершённый вызов, потерять критерий
готовности или принять текст из tool output за инструкцию. Надёжность начинается с
того, что переходами задачи между состояниями управляет приложение, а не восстанавливает
модель догадкой.

## CONCEPT

### Не одна «память», а разные виды состояния

Слово «память» слишком широкое. В этом уроке мы разделим сущности по их назначению:

| Сущность | Простой вопрос | Пример | Правило |
|---|---|---|---|
| `goal` | Какого результата хотим? | Подготовить решение для `run-review` | Не содержит готового списка tool calls |
| `plan` | Что предположительно делать дальше? | Прочитать решение; при необходимости диагностировать проверку | Может пересматриваться после Observation |
| `working_facts` | Что сейчас известно о конкретной задаче? | `release.decision = review` | Именованные предметные поля с понятным источником |
| `execution_trace` | Что фактически произошло? | `Action(read-decision) ↔ Observation(...)` | Журнал только с добавлением новых записей, а не список будущих шагов |
| `checkpoint` | Из какого состояния продолжать после restart? | Plan version, statuses, facts, trace | Сохраняемый снимок состояния задачи |
| `long-term memory` | Что стоит перенести между разными задачами? | Устойчивое предпочтение или проверенное знание | Отдельные правила доверия и срок жизни из 4.2 |

**Рабочие факты** — это не всё, что когда-либо увидел агент. Это минимальный набор
именованных значений, нужных для текущего решения. Например,
`release.failed_checks = ["security"]` полезно следующему шагу. Полный stack trace,
случайный фрагмент ответа модели и имя пользователя, предложенное самой моделью, не
становятся рабочими фактами автоматически.

**Execution trace** тоже не является рабочей или долговременной памятью. Trace отвечает
«что произошло и с каким ID», а working facts — «что мы из этого используем сейчас».
Это append-only журнал: новые записи добавляются, а уже произошедшие действия не
переписываются задним числом. Один и тот же Observation остаётся в trace как
доказательство, но в рабочих фактах может быть представлен двумя проверенными полями.

**Checkpoint** — не новая разновидность знания. Это способ сохранить состояние задачи
на границе перехода: цель, текущую версию плана, статусы шагов, факты, trace и финальный
статус. После загрузки приложение продолжает переходы из сохранённого `TaskState`, а не
просит модель заново сочинить прошлое.

`TaskState` — один объект, который объединяет goal, текущий plan, working facts,
execution trace и общий статус **одной** задачи. Именно его сериализует checkpoint.

### Из чего состоит проверяемый план

Пункт плана должен быть наблюдаемым и проверяемым. В reference-коде `PlanStep` содержит:

| Поле | Зачем оно нужно |
|---|---|
| `step_id` | Стабильно связать шаг, Action, Observation и checkpoint |
| `objective` | Объяснить предметную цель шага, а не только имя функции |
| `tool` и `arguments` | Подготовить конкретный вызов через runtime 7.1 |
| `success_criterion` | Решить по structured result, выполнен ли шаг |
| `depends_on` | Не исполнить шаг раньше необходимых предшественников |
| `status` | Отделить ожидающее, начатое, завершённое и заблокированное |

Используем статусы `pending`, `in_progress`, `completed`, `blocked` и `skipped`.
Новый шаг начинается как `pending`. Перед передачей Action исполнителю он становится
`in_progress`. Только соответствующий валидный Observation переводит его в
`completed`. Ошибка инструмента или нарушение схемы приводит к `blocked`, а не к
правдоподобному вымышленному финалу.

`plan_version` увеличивается, когда меняется **структура будущего маршрута**: например,
после `decision=review` появляется новый диагностический шаг. Обычная смена статуса
`pending → in_progress → completed` не создаёт новую версию плана. Иначе номер версии
описывал бы каждое техническое сохранение, а не содержательный пересмотр.

### Переход состояния после Observation

```text
goal + TaskState
       │
       ▼
 decide_next() ──► PlanStep: pending → in_progress
       │                          │
       │                 checkpoint до вызова
       ▼                          │
 executor 7.1: проверка tool, args, access policy, budget
       │
       ▼
 Observation(action_id, ok, output/error)
       │
       ▼
 apply_observation()
       ├── дополнить append-only trace
       ├── проверить structured result по success criterion
       ├── обновить именованные working facts
       ├── завершить или заблокировать текущий шаг
       ├── при новых фактах пересмотреть будущий plan
       └── сохранить checkpoint после результата
```

Слой состояния (state layer) 7.2 не должен повторять защиту 7.1. `decide_next`
предлагает `Action`, но именно инъецированный executor проверяет allowlist, named
arguments, trusted context, server-side authorization и step budget. Если новый слой
напрямую импортирует domain handler, он обходит проверенную в 6.5 границу.

### Почему checkpoint нужен до и после вызова

Сохранение только после инструмента оставляет опасное окно. Процесс может упасть после
побочного эффекта (side effect), но до записи Observation. Поэтому reference сохраняет шаг как
`in_progress` **до** исполнения, а затем сохраняет Observation и новый статус.

Есть три разных случая:

1. `completed` и Observation сохранены — шаг доказан, при resume повторять его нельзя.
2. `pending` — Action ещё не начинался, шаг можно выбрать после проверки зависимостей.
3. `in_progress`, но Observation отсутствует — результат неоднозначен: side effect мог произойти. Автоматический повтор запрещён до сверки факта во внешней системе (reconciliation) или проверки ключа идемпотентности, по которому система узнаёт тот же запрос.

Checkpoint сам по себе не гарантирует «выполнить ровно один раз» (exactly-once). Для
write-capability нужны идемпотентность, стабильный ID запроса для корреляции и способ
сверить фактическое состояние внешней системы. В BUILD IT инструменты read-only, но мы
всё равно блокируем неоднозначный повтор: так одна и та же модель состояния останется
безопасной, когда в 7.3 появятся подтверждаемые действия.

## РАЗБОР ПО ШАГАМ

Перед чтением трасс предположи: сколько tool calls понадобится для `run-ready` и
`run-review`? В хорошем плане ответ зависит не от длины заранее выданного `ops`, а от
первого Observation.

### Ветка `run-ready`: план не расширяется

Начальная цель высокоуровневая:

```python
goal = {
    "objective": "prepare_release_readiness",
    "run_id": "run-ready",
}
```

В ней нет `ops`. Детерминированный planner создаёт короткую первую версию:

```text
plan_version = 1
read-decision: pending
```

`decide_next` отмечает шаг `in_progress`, executor возвращает
`{decision: "publish", failed_checks: []}`, а `apply_observation` проверяет обязательные
поля. После этого:

```text
read-decision: completed
working_facts:
  release.decision = publish
  release.failed_checks = []
status = completed
plan_version = 1
```

Новый шаг не нужен, поэтому версия остаётся первой. Один tool call приводит к финалу.

### Ветка `run-review`: Observation меняет план

Первая версия такая же, но Observation другой:

```text
read-decision
← {decision: "review", failed_checks: ["security"]}
```

Текущий шаг завершается, два поля становятся рабочими фактами, а planner добавляет
зависимый шаг:

```text
plan_version = 2
read-decision:       completed
diagnose-security:  pending, depends_on=[read-decision]
```

Следующий Action вызывает `get_check_report` только для найденной проверки. Валидный
ответ сохраняет `release.diagnostic_status` и `release.diagnostic_summary`, завершает
второй шаг и всю задачу. Так plan остаётся гипотезой: его будущая часть уточнилась из
данных среды, а уже произошедшая часть не была переписана.

### Restart между двумя шагами

```text
process 1:
  save read-decision=in_progress
  execute get_release_decision
  save read-decision=completed, diagnose-security=pending, plan_version=2

restart

process 2:
  load TaskState
  skip completed read-decision
  execute pending diagnose-security
```

Тест записывает имена фактически вызванных tools и получает ровно
`["get_release_decision", "get_check_report"]`. Первый вызов после restart не
повторяется. Отдельный failure test сохраняет `read-decision=in_progress` без Observation
и убеждается, что resume требует reconciliation вместо слепого повтора.

## BUILD IT

**Задание:** поверх контракта 7.1 собери state layer, который различает план, рабочие
факты и trace, пересматривает маршрут после Observation и продолжает задачу из JSON
checkpoint. Только стандартная библиотека и `pytest`; сеть и LLM не нужны.

> **Перед запуском.** Сам курс клонировать не нужно. Создай личную папку
> `ai-native-work/course-work/phase-7/7.2-planning-state/` и внутри неё `code/`.
> Перенеси из своей работы 7.1 только контракты `Action`, `Observation` и безопасный
> executor либо временно используй офлайн test double этого урока.

Сначала скопируй тесты со страницы урока и запусти их красными. Затем реализуй:

- `PlanStep` с ID, целью, tool, именованными аргументами, success criterion, dependencies и status;
- `TaskState` с высокоуровневой goal, `plan_version`, plan, working facts, execution trace, status и final answer;
- `create_initial_state(goal)`, который принимает цель без `ops` и создаёт только первый необходимый шаг;
- `decide_next(state)`, который выбирает допустимый `pending` step, проверяет зависимости и не повторяет `completed`/неоднозначный `in_progress`;
- `apply_observation(state, observation)`, который проверяет корреляцию и схему результата, обновляет trace и факты, а при необходимости создаёт новую версию плана;
- `JsonCheckpointStore`, который сначала целиком пишет временный JSON-файл, а затем одной операцией заменяет старый checkpoint: читатель увидит старую или новую полную версию, но не половину записи;
- `advance_task(...)`, сохраняющий checkpoint до и после вызова executor;
- `reference_executor` как офлайн test double среды, а не как production security boundary.

Не копируй в state весь provider response. Сначала назови предметные поля, которые
потребуются следующему решению, затем проверяй их схему и сохраняй только их. Tool error
и невалидный structured result — наблюдаемые данные о неуспехе, а не повод выдумать
`publish`.

```bash
cd ai-native-work/course-work/phase-7/7.2-planning-state
pytest code -q
python code/planner_agent.py
```

**Готово, когда восемь поведенческих проверок доказывают:**

- goal остаётся высокоуровневой и не содержит готовых операций;
- разные первые Observation ведут к короткой и расширенной веткам плана;
- пересмотр структуры увеличивает `plan_version` и создаёт dependency;
- рабочие факты имеют предметные имена и не подменяются `step_0`;
- невалидный result и tool error блокируют задачу без сфабрикованного ответа;
- шаг с невыполненной зависимостью не исполняется;
- после checkpoint/restart завершённый tool не вызывается повторно;
- `in_progress` без сохранённого Observation требует reconciliation.

Внизу, в [«Исходниках урока»](#lesson-files), есть тесты-ТЗ, reference-реализация и
шаблон итогового record. Сначала добейся red → green в своей папке; эталон используй
для сверки контракта, а не как замену собственной диагностике.

### Самостоятельный перенос из 7.1

Возьми одну **read-only capability** из своего `agent-loop-contract.md`. Не импортируй
её domain handler прямо в planner. Передай в `advance_task` executor из 7.1, который
вызывает MCP client adapter, а server применяет access policy.

Самостоятельно определи высокоуровневую цель, первый минимальный шаг, именованные рабочие
факты и критерий завершения. Затем придумай два валидных Observation, которые должны
дать разные маршруты. Повтори allow- и deny-сценарии 6.5 на настоящем transport и
убедись, что model-controlled state не содержит actor, roles или scopes из trusted
context.

## USE IT

В production первый план и его пересмотр может предлагать модель. Но модель не становится
владельцем жизненного цикла задачи. Приложение валидирует её ответ в строгую структуру `PlanStep`,
проверяет доступные capability и dependencies, меняет version, сохраняет checkpoint и
решает, можно ли продолжать.

Концептуальная граница выглядит так:

```python
proposal = provider_adapter.propose_plan(
    goal=state.goal,
    working_facts=state.working_facts,
    current_plan=state.plan,
    tool_schemas=TOOL_SCHEMAS,
)

validated_steps = validate_plan_proposal(proposal)
state.plan = merge_future_steps(state.plan, validated_steps)
state.plan_version += 1
checkpoint.save(state)
```

Модель может предложить декомпозицию, но не должна самостоятельно объявлять прошлый
шаг выполненным, менять append-only trace, подставлять trusted identity или обходить
executor 7.1. Success criteria и допустимые side effects остаются решением владельца
системы.

Важно не спутать платформенные механизмы с domain-specific TaskState:

- [OpenAI Agents SDK Sessions](https://openai.github.io/openai-agents-python/sessions/) сохраняют историю диалога между runs, но не определяют ваши статусы шагов, success criteria, рабочие факты и правила resume.
- [Anthropic memory tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool) даёт модели клиентский интерфейс чтения и записи файлов в `/memories`; операции исполняет приложение, а содержимое не становится автоматически проверенным планом или checkpoint задачи.
- Long-term memory из 4.2 переносит отобранное знание между задачами; working facts этого урока живут внутри одной задачи и имеют другой жизненный цикл.

Необязательный реальный эксперимент: подключи model-backed planner только к read-only
capability, выполни первый шаг, сохрани checkpoint, полностью останови процесс и запусти
его снова. Критерий успеха — второй процесс продолжает pending-ветку, а trace и журнал
MCP подтверждают, что completed call не повторился.

### Как использовать ИИ: 4D

- **Delegation:** поручай ИИ черновик dataclass, JSON-схемы plan proposal, тестов ветвления или adapter к провайдеру; критерии завершения, жизненный цикл фактов и допустимые side effects определяй сам.
- **Description:** передай высокоуровневую goal, capability schemas, контракт Observation, step budget 7.1, поля checkpoint и правило «completed не повторять, ambiguous in_progress не replay».
- **Discernment:** ищи готовый `ops` внутри goal, неизменяемый «план-истину», смешение trace с рабочими фактами, доверие ко всей истории чата и повтор вызова после restart.
- **Diligence:** проверь diff, получи red → green, запусти обе ветки, открой JSON checkpoint, смоделируй restart и повтори allow/deny через MCP; уверенный текст модели не заменяет эти доказательства.

## SHIP IT

**Артефакт:** план, состояние и доказательство resume →
[`outputs/plan-and-state-record.md`](../outputs/plan-and-state-record.md)

Заполни record на своей capability: высокоуровневая цель, success criterion, две версии
плана, источник (provenance) рабочих фактов, trace до и после restart, доказательство
отсутствия повтора completed step и способ сверки для `in_progress`.

В конце назови один потенциально опасный шаг, которому нужен `approval_required`. В
7.3 этот сериализуемый TaskState станет точкой pause: приложение сохранит запрос на
подтверждение, человек примет решение, а агент продолжит тот же план, не восстанавливая
его из чата.

## ЧАСТЫЕ ОШИБКИ

- **Передать `goal["ops"]`.** Тогда planner только переупаковывает заранее заданный workflow и не демонстрирует пересмотр маршрута по Observation.
- **Считать начальный план окончательной истиной.** План описывает предполагаемое будущее; новые проверенные факты должны иметь возможность изменить его невыполненную часть.
- **Смешать план, trace и working facts.** Список будущих шагов, журнал произошедшего и текущее предметное состояние отвечают на разные вопросы и имеют разный жизненный цикл.
- **Назвать историю чата TaskState.** История помогает модели держать контекст, но сама не задаёт statuses, dependencies, критерий завершения и правила безопасного resume.
- **Доверять `ok=True` без проверки output.** Транспортный успех не доказывает предметный контракт; отсутствующие обязательные поля должны блокировать переход.
- **Повторить `in_progress` после restart.** Процесс мог упасть после side effect; сначала сверяй внешнее состояние или idempotency key.
- **Сохранять всё в long-term memory.** Tool output может содержать недоверенный текст, секреты и устаревающие данные; рабочие факты задачи не получают вечный срок жизни автоматически.
- **Обойти runtime 7.1.** Planner выбирает шаг, но allowlist, schema, budget, trusted context и access policy остаются на границе исполнения.

## ПРОВЕРЬ СЕБЯ

Ответь на вопросы — проверка сразу, с пояснением.

{{quiz}}

## Дополнительное чтение

- [Anthropic — Agent SDK overview](https://platform.claude.com/docs/en/agent-sdk/overview) — agent loop, контекст, инструменты.
- [Anthropic — Memory tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool) — память агента между сессиями.
- [ReAct (arXiv 2210.03629)](https://arxiv.org/abs/2210.03629) — рассуждение и действие как основа агента.
- [Huang et al., 2024 — Understanding the Planning of LLM Agents: A Survey](https://arxiv.org/abs/2402.02716) — таксономия планирования: декомпозиция, выбор плана, рефлексия, память.
- [LangGraph — Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) — checkpointers (короткая память) + stores (длинная), resume / HITL / fault-tolerance в реальном фреймворке.
- [Anthropic — Effective harnesses for long-running agents (2025)](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) — многосессионность, трекинг прогресса, восстановление контекста.
- [DeepLearning.AI — Agentic AI (Andrew Ng, 2025)](https://www.deeplearning.ai/courses/agentic-ai) — паттерны Reflection / Tool / Planning / Multi-agent на чистом Python.
- [Towards AI — Memory Management in LangGraph (Medium)](https://pub.towardsai.net/understanding-memory-management-in-langgraph-a-practical-guide-for-genai-students-b3642c9ea7e1) — практический разбор памяти агента.

---
**Часы:** ~7 · **DoD:** 8 поведенческих тестов зелёные; `run-ready` и `run-review` дают разные версии плана; checkpoint/restart не повторяет completed step; неоднозначный `in_progress` требует reconciliation; личная read-only capability проходит через runtime/MCP 7.1; `plan-and-state-record.md` заполнен и содержит handoff в 7.3. ✅ **Урок готов**
