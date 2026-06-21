---
name: agent-eval
description: "Оценка агента курса AI Native: прогон по тест-сету, метрики успеха, сравнение версий и детект регрессий. Триггеры: «/agent-eval», «оцени агента», «сравни версии агента», «есть ли регрессия», «прогони eval агента». Артефакт урока 7.5."
---

# agent-eval — оценка агента и защита от регрессий

Превращает «вроде стало лучше» в число: фиксированный тест-сет + метрики → сравнение версий агента и блок регрессий.

## Как пользоваться

1. Собери тест-сет `cases = [{"input": ..., "expected": ...}, ...]` (реальные задачи + эталоны, включая граничные).
2. Заведи версии как функции `versions = {"v1": agent_fn1, "v2": agent_fn2}` (в проде — вызов агента).
3. Выбери метрику (`task_success` или своя: tool-correctness, число шагов).
4. Прогон и сравнение:

```bash
python -c "import agent_eval as a; \
print(a.compare_versions({'good': lambda x: str(eval(x)), 'bad': lambda x: '?'}, \
[{'input':'2+2','expected':'4'}]))"
```

5. Покажи `success_rate`, рейтинг версий и `has_regression(baseline, candidate, cases)`.

## Файлы

- `agent_eval.py` — `evaluate_agent`, `compare_versions`, `has_regression`.

## Когда применять

Перед мерджем правки агента/промпта/инструмента — прогони eval, поставь порог в CI, блокируй регрессии. Online-evals в проде — LangSmith/Phoenix (урок 10.4).
