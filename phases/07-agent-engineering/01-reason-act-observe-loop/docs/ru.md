# Урок 7.1 · Цикл reason → act → observe

**Фаза 7 — Agent Engineering** · **Результат фазы:** Собрать надёжного агента с памятью, планированием, human-in-the-loop и guardrails.
<!-- exercise -->

**Результат урока:** собрать ограниченный agent runtime, в котором decision policy
выбирает следующее действие из цели и видимого execution trace, runtime проверяет
инструмент и именованные аргументы, сопоставляет действие с результатом, позволяет
policy исправиться после безопасной ошибки и останавливает новый side effect после
исчерпания бюджета.

**Опоры:** цикл tool use и structured result из 6.1; защищённая read-only capability,
trusted context и server-side access policy из 6.5. BUILD IT работает офлайн, без
API-ключа и сети. Для необязательного переноса на LLM в USE IT понадобится ключ
выбранного провайдера.

**Это вход в Фазу 7.** В Фазе 6 программа научилась безопасно вызывать отдельный
инструмент. Теперь она должна сама решать, достаточно ли результата, какой разрешённый
инструмент вызвать следующим и когда остановиться. План и отдельную память добавим в
7.2, подтверждение опасных действий — в 7.3.

Открой раздел `В 7.1 — reason → act → observe` своего `phase-6-dossier.md`. Для
личного переноса выбери оттуда **одну разрешённую read-only capability**. Agent runtime
должен обращаться к ней через MCP client adapter, а не импортировать domain handler:
иначе он обойдёт server-side policy, которую ты доказывал в 6.5.

> **Главная мысль.** Агент — не «особая модель», а управляемый цикл: выбрать
> следующее действие → выполнить его через ограниченный runtime → увидеть результат →
> скорректировать следующий шаг или завершить задачу.

## PROBLEM

Слово «агент» легко превращает обычную программу в магию: кажется, будто достаточно
подключить LLM к нескольким функциям — и она сама надёжно доведёт любую цель до
результата. Но между ответом модели и реальным действием остаются инженерные вопросы:

- что именно модель имеет право вернуть;
- кто проверит имя инструмента и его аргументы;
- как связать вызов с соответствующим результатом;
- увидит ли policy ошибку и сможет ли изменить решение;
- что остановит следующий вызов, если цикл застрял;
- где находится доверенная identity и кто применяет access policy.

Если ответы не зафиксированы, «агент» либо остаётся чатом, либо становится
неограниченным циклом побочных эффектов. Поэтому сначала соберём маленький runtime на
чистом Python и проверим его детерминированной policy. LLM подключим только после того,
как контракт цикла станет видимым и тестируемым.

## CONCEPT

### Семь частей одного витка

| Часть | Что это | Кто контролирует |
|---|---|---|
| `goal` | Наблюдаемый результат, которого нужно достичь | Пользователь или приложение |
| `decision_policy` | Выбор следующего действия по цели и уже видимым результатам | Детерминированный код или модель |
| `Action` | Команда `tool` либо завершение `final` | Возвращает policy, проверяет runtime |
| `tool` | Ограниченная capability с именованным контрактом | Приложение / MCP server |
| `Observation` | Структурированный успех или безопасная ошибка | Формирует runtime |
| `execution_trace` | Последовательность `Action ↔ Observation` текущего запуска | Runtime |
| `step budget` | Максимум попыток действия до остановки | Владелец приложения |

Здесь **decision policy** означает политику выбора следующего шага. Это не то же самое,
что **access policy** из 6.5: первая предлагает действие, вторая решает, разрешено ли
его выполнять для доверенного субъекта и объекта. Decision policy не может отменить
server-side authorization.

### Что означают reason, act и observe

```text
goal + execution_trace
          │
          ▼
  decision_policy                 reason: выбрать следующий наблюдаемый шаг
          │
          ├── Action(final, answer) ───────────────► результат
          │
          └── Action(tool, action_id, arguments)
                              │
                              ▼
                     runtime checks                 граница исполнения
                              │
                              ▼
                         tool / adapter              act
                              │
                              ▼
             Observation(action_id, ok, output/error)
                              │
                              └──────────────► execution_trace ──┐
                                                                └─ новый виток
```

- **Reason** в этом уроке — не просьба раскрыть скрытую цепочку мыслей модели. Это наблюдаемое решение: `final` или конкретный `tool action` с ID и аргументами.
- **Act** начинается только после проверок runtime. Модель не получает прямой callable и не исполняет код сама.
- **Observe** означает, что успех или ошибка превращаются в данные и возвращаются decision policy. Сырой exception не должен автоматически попадать в контекст или лог.

`execution_trace` — журнал одного запуска, а не полноценная память агента. Он нужен,
чтобы следующий шаг видел предыдущие действия и результаты. Именованную рабочую и
долговременную память, которая переживает отдельные шаги или запуски, добавим в 7.2.

### Workflow, agent runtime и агент — не одно и то же

В workflow маршрут заранее задан кодом: сначала A, затем B, затем C. Агент выбирает
маршрут во время исполнения по цели и промежуточным результатам. Это не означает, что
агент всегда лучше: фиксированный путь проще проверять и обычно правильнее для
предсказуемой задачи.

BUILD IT использует `ReleaseDecisionPolicy` — детерминированный **test double** вместо
модели. В нём всё ещё описаны допустимые ветки, поэтому офлайн-демо само по себе не
доказывает автономность LLM. Оно доказывает более важную инженерную часть: runtime не
зашивает последовательность вызовов и способен выполнить разные маршруты, выбранные
policy после наблюдения. В USE IT тот же контракт получает model-backed policy.

Сравни две цели:

```text
Плохо: {ops: [get_release_decision, get_check_report, final]}
       Маршрут уже передан исполнителю — это последовательный workflow.

Хорошо: {run_id: "run-review"}
        Policy сначала читает решение, а следующий шаг выбирает по Observation.
```

> **Врезка: три режима человек–ИИ (AI Fluency).** В **Automation** человек задаёт
> конкретный повторяемый путь. В **Augmentation** человек и ИИ итеративно выбирают
> шаги вместе. В **Agency** человек задаёт цель, доступные capability и границы, а
> система выбирает следующий шаг внутри этих границ. Переход к Agency не отменяет
> ответственность человека: чем больше свобода выбора, тем важнее наблюдаемый trace,
> budgets и подтверждения из 7.3.

### Инварианты минимального runtime

1. Аргументы инструмента остаются объектом с именованными полями. Нельзя превращать `{"run_id": "run-42"}` в tuple значений: порядок не является контрактом.
2. Каждый tool action имеет уникальный `action_id`; observation содержит тот же ID.
3. Неизвестный инструмент и неверные аргументы не приводят к вызову callable.
4. Ошибка инструмента становится безопасным observation, чтобы policy могла изменить следующий шаг. Внутренний текст исключения в trace не копируется.
5. Каждая попытка tool action расходует шаг бюджета, даже если runtime её отклонил.
6. После последнего observation policy может завершить задачу, но новый tool action при исчерпанном бюджете блокируется **до** side effect.
7. Identity, роли и scopes поступают в MCP adapter из доверенного контекста приложения, а не из аргументов, предложенных моделью.

## РАЗБОР ПО ШАГАМ

Референсная цель содержит только идентификатор прогона:

```python
goal = {"run_id": "run-review"}
```

Она не содержит готового плана. Policy должна увидеть результат первой capability и
только после этого выбрать маршрут.

### Ветка 1: релиз готов

```text
trace пуст
reason  → Action("tool", id="decision-1",
                 tool="get_release_decision",
                 arguments={"run_id": "run-ready"})
act     → adapter/server применяет access policy и читает решение
observe → Observation(id="decision-1", ok=True,
                      output={"decision": "publish", "failed_checks": []})
reason  → Action("final", answer={"decision": "publish", ...})
```

Один tool step: дополнительная диагностика не нужна.

### Ветка 2: нужна проверка человеком

```text
decision-1 → get_release_decision({run_id: "run-review"})
           ← {decision: "review", failed_checks: ["security"]}

report-security → get_check_report({run_id: "run-review", check: "security"})
                ← {status: "failed", summary: "...human review"}

final → {decision: "review", summary: "...human review"}
```

Здесь два tool step. Второго вызова нет в `goal`: он появился после первого
observation. Это и есть ключевая петля урока.

### Ветка 3: исправимая ошибка

Если первый вызов временно завершается ошибкой, runtime не падает и не переносит сырой
exception в trace:

```text
decision-1 → Observation(ok=False, error_code="tool_error")
decision-2 → повторный get_release_decision(...)
           ← Observation(ok=True, output={decision: "publish", ...})
final
```

Референсная policy допускает только одну повторную попытку. Retry без границы создал бы
новую петлю, поэтому более сложную retry/backoff policy отложим до урока 7.4.

## BUILD IT

**Задание:** собери минимальный agent runtime и докажи три маршрута — быстрый финал,
диагностическую ветку и восстановление после одной безопасной ошибки. Только стандартная
библиотека, без сети и LLM.

> **Перед запуском.** Сам курс клонировать не нужно. Работай в личной папке
> `ai-native-work/course-work/phase-7/7.1-agent-loop/`, создай внутри `code/` и
> скопируй туда тесты со страницы урока. Нужны Python 3 и `pytest`.

Сначала создай `code/agent_loop.py` по контракту:

- `Action(kind, action_id, tool, arguments, answer)` — решение policy;
- `Observation(action_id, ok, output, error_code)` — результат попытки;
- `Step(action, observation)` — одна коррелированная запись trace;
- `run_agent(goal, tools, decision_policy, max_steps)` — цикл до `final` или бюджета;
- `_execute(...)` — проверка allowlist, объектных аргументов и сигнатуры до вызова;
- `ReleaseDecisionPolicy` — офлайн test double с ветками `publish`, `review` и одной повторной попыткой после `tool_error`;
- `make_release_decision_adapter(...)` — граница между публичными аргументами action и trusted context MCP-клиента.

Не начинай с эталона. Скопируй `test_agent_loop.py`, запусти красные тесты и реализуй
контракт по одному наблюдаемому свойству.

```bash
cd ai-native-work/course-work/phase-7/7.1-agent-loop
pytest code -q
python code/agent_loop.py
```

**Готово, когда тесты доказывают:**

- `publish` заканчивается после одного tool step, а `review` выбирает второй инструмент;
- `action_id` совпадает с `observation.action_id`, аргументы остаются именованными;
- неизвестный tool и неверная схема аргументов не вызывают защищённую функцию;
- ошибка tool становится `tool_error`, после чего policy один раз исправляется;
- исчерпанный budget не допускает следующий side effect;
- повторный `action_id` отклоняется до второго исполнения;
- MCP adapter передаёт модели только `run_id`, а actor/scopes получает из trusted context приложения.

Внизу, в [«Исходниках урока»](#lesson-files), — тесты-ТЗ, эталон и заготовка итогового
артефакта. Можно собрать самому, свериться после попытки или делегировать реализацию ИИ,
но критерий приёмки остаётся одним и тем же.

### Самостоятельный перенос capability из 6.5

Офлайн-функции — только учебная среда. После зелёных тестов возьми одну read-only
capability из `phase-6-dossier.md` и замени соответствующую функцию adapter-ом:

```python
protected_tool = make_release_decision_adapter(
    call_capability=mcp_client_call,
    trusted_context=current_session_context,  # не приходит от модели
)

tools = {"get_release_decision": protected_tool}
```

Сопоставь своё имя capability, public argument schema и structured result. Не копируй
пример `run_id`, если твоя граница — dataset, document или project. Сначала повтори
allow/deny проверки 6.5 на реальном transport, затем запусти agent loop. Dangerous
capability, помеченную `approval_required`, пока не подключай — её место в 7.3.

## USE IT

С настоящей моделью стабильными остаются runtime, `Action`, `Observation` и domain
tools. Добавляется **provider adapter**, который переводит нативный ответ API в Action
и observation обратно в формат следующего запроса. Это важнее формулы «меняется только
policy»: у провайдеров различаются content blocks, stop reasons и формат tool result.

Концептуальный adapter выглядит так:

```python
def model_decision_policy(goal, execution_trace):
    response = provider_adapter.decide(
        goal=goal,
        execution_trace=execution_trace,
        tool_schemas=TOOL_SCHEMAS,
    )

    if response.kind == "tool":
        return Action(
            kind="tool",
            action_id=response.call_id,
            tool=response.name,
            arguments=response.arguments,  # dict, не tuple(values)
        )
    if response.kind == "final":
        return Action(kind="final", answer=response.text)
    raise AgentError(f"unsupported provider outcome: {response.kind}")
```

Внутри конкретного adapter нужно проверить stop reason, найти все tool-use blocks,
сохранить provider call ID, передать `input` как объект и вернуть соответствующий
tool result. Нельзя брать `response.content[0]` без проверки: первым блоком может быть
текст, а tool-вызовов может оказаться несколько. Для первого упражнения либо явно
запрещай несколько одновременных вызовов понятной ошибкой, либо расширяй контракт — не
теряй молча лишние blocks.

Модель по-прежнему не получает trusted identity, scopes или MCP server callable.
Provider adapter предлагает Action, agent runtime проверяет локальный контракт, MCP
adapter вызывает capability, а server снова применяет access policy.

### Как использовать ИИ: 4D

- **Delegation:** можно поручить ИИ черновик dataclass, provider adapter или тестов. Нельзя делегировать решение о том, какие capability и side effects допустимы.
- **Description:** передай контракт `Action ↔ Observation`, tool schemas, budget, ожидаемые ветки и запрет на identity/scopes в model-controlled arguments.
- **Discernment:** проверь, выбирается ли маршрут после observation или уже зашит в goal; может ли неизвестный tool выполнить код; совпадают ли call IDs; не потерялись ли аргументы при преобразовании ответа провайдера.
- **Diligence:** прочитай diff, добейся red → green, запусти обе ветки демо, затем повтори allow и deny через настоящий MCP transport. Фраза ИИ «guardrails добавлены» не является доказательством.

## SHIP IT

**Артефакт:** контракт и доказательство agent loop →
[`outputs/agent-loop-contract.md`](../outputs/agent-loop-contract.md)

В артефакте зафиксируй цель, разрешённые capability, Action/Observation contract,
успешную и ошибочную трассы, stop condition, budget и MCP boundary. Это не `skill` из
Фазы 4: обычный Markdown-файл не становится skill без `SKILL.md` и его контракта.

В 7.2 передай execution trace и явно назови, какого состояния не хватает для длинной
задачи. Не называй trace долговременной памятью: следующий урок введёт отдельные
working memory и plan.

## ЧАСТЫЕ ОШИБКИ

- **Передать готовый список шагов в goal.** Тогда policy исполняет workflow, а не выбирает маршрут по наблюдениям.
- **Называть reason скрытым рассуждением.** Runtime нужен наблюдаемый Action, а не внутренний монолог модели.
- **Превратить object arguments в positional tuple.** Теряются имена и надёжная проверка tool schema.
- **Поднять exception на любой ошибке инструмента.** Исправимая ошибка должна стать безопасным observation. Ошибка контракта самого runtime может останавливать запуск.
- **Считать отклонённый action бесплатным.** Он тоже расходует шаг: иначе policy может бесконечно отправлять невалидные вызовы.
- **Проверить budget после вызова.** Guardrail должен остановить следующий side effect до исполнения инструмента.
- **Смешать decision policy и access policy.** Первая предлагает шаг; только вторая, работающая на доверенной границе, разрешает доступ.
- **Назвать trace памятью.** Trace объясняет один запуск; план и отдельную память для длинной задачи добавим в 7.2.

## ПРОВЕРЬ СЕБЯ

Ответь на вопросы — проверка сразу, с пояснением.

{{quiz}}

## Дополнительное чтение

Это факультативный раздел: для завершения урока не нужно читать ни одного материала и тем более весь список. Выбери одну ветку по своему вопросу — понять границу «workflow или agent», сопоставить учебный runtime с API одного провайдера, посмотреть независимую реализацию или заглянуть в следующие уроки.

**Понять механизм и границу применимости**

- [Anthropic — Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) — прочитай только `What are agents?`, `When (and when not) to use agents` и `Agents`: сопоставь фиксированный workflow, динамический маршрут, environmental feedback и stopping conditions с контрактом урока.
- [Yao et al. — ReAct (arXiv 2210.03629)](https://arxiv.org/abs/2210.03629) — начни с abstract и схемы чередования reasoning/action/observation; это исследовательский первоисточник паттерна, а не требование сохранять скрытые рассуждения модели в production trace.

**Сопоставить runtime с API одного провайдера**

- [Claude Platform — How tool use works](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works) и [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) — открой `The agentic loop` и `Handling results from client tools`: проследи `stop_reason`, один или несколько `tool_use`, объект `input`, ID вызова и связанный `tool_result`.
- [OpenAI — Function calling](https://developers.openai.com/api/docs/guides/function-calling) — прочитай `How it works` и `Handling function calls`: сопоставь `call_id` и `function_call_output` с `Action.action_id` и `Observation`, не перенося в код названия полей другого API.
- [Google Gemini — Function calling](https://ai.google.dev/gemini-api/docs/function-calling) — изучи manual function calling loop и сравни `functionCall`/`functionResponse` с тем же provider-neutral контрактом; automatic calling оставь как альтернативу после того, как понимаешь ручной цикл.

**Посмотреть независимую реализацию и production-паттерны**

- [Thorsten Ball — How to Build an Agent](https://ampcode.com/notes/how-to-build-an-agent) — дойди от краткого контракта tool use до цикла `Run` и `executeTool`: это подробная реализация coding agent на Go без агентного фреймворка, а не эталон security boundary.
- [HumanLayer — Own your control flow](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-08-own-your-control-flow.md) и [Compact Errors into Context Window](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-09-compact-errors.md) — сравни собственный loop, break/continue, error counter и передачу ошибки обратно модели с budget и безопасным `error_code` урока; сырой stack trace копировать не нужно.
- [Chip Huyen — Agent Failure Modes and Evaluation](https://huyenchip.com/2025/01/07/agents.html#agent-failure-modes-and-evaluation) — сосредоточься на invalid tool, invalid parameters, tool failures и efficiency: список помогает превратить ещё не покрытые риски в будущие тесты 7.4–7.5.

**Заглянуть в 7.2, не превращая материал в пререквизит**

- [Lilian Weng — Agent System Overview](https://lilianweng.github.io/posts/2023-06-23-agent/#agent-system-overview) — прочитай обзор planning, memory и tool use, чтобы увидеть, какие компоненты будут нарастать поверх loop; подробности planning и memory относятся уже к следующему уроку.

---
**Часы:** ~5 · **DoD:** восемь reference-тестов зелёные; обе ветки и восстановление
объясняются по trace; личная read-only capability вызывается через MCP adapter без
model-controlled identity; заполнен `agent-loop-contract.md` с handoff в 7.2. ✅ **Урок готов**
