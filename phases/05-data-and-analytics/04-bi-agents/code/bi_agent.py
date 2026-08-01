"""Детерминированный BI-планировщик для урока 5.4.

Планировщик не пишет произвольный SQL. Он выбирает следующий разрешённый
аналитический intent по предыдущему наблюдению, сохраняет trace и останавливается
по явной причине.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from typing import Any


SEMANTIC = {
    "version": "1.1",
    "owner": "course-team",
    "metric_ids": {
        "paid_revenue": {
            "unit": "RUB",
            "definition": "Сумма оплаченной выручки",
            "required_filter": {"status": "paid"},
        }
    },
    "periods": ["Q1", "Q2"],
    "dimension_ids": ["region", "product"],
    "investigation_order": ["region", "product"],
}

# Это уже проверенные наблюдения semantic executor, а не сырые строки заказов.
# Q2 сохраняет результат предыдущих уроков: 150 + 30 + 20 = 200 RUB.
DEMO_FACTS = [
    {"quarter": "Q1", "region": "Москва", "product": "Basic", "paid_revenue": 70},
    {"quarter": "Q1", "region": "Москва", "product": "Pro", "paid_revenue": 100},
    {"quarter": "Q1", "region": "Питер", "product": "Basic", "paid_revenue": 30},
    {"quarter": "Q1", "region": "Питер", "product": "Pro", "paid_revenue": 50},
    {"quarter": "Q1", "region": "Казань", "product": "Basic", "paid_revenue": 10},
    {"quarter": "Q1", "region": "Казань", "product": "Pro", "paid_revenue": 10},
    {"quarter": "Q2", "region": "Москва", "product": "Basic", "paid_revenue": 70},
    {"quarter": "Q2", "region": "Москва", "product": "Pro", "paid_revenue": 80},
    {"quarter": "Q2", "region": "Питер", "product": "Basic", "paid_revenue": 20},
    {"quarter": "Q2", "region": "Питер", "product": "Pro", "paid_revenue": 10},
    {"quarter": "Q2", "region": "Казань", "product": "Basic", "paid_revenue": 10},
    {"quarter": "Q2", "region": "Казань", "product": "Pro", "paid_revenue": 10},
]


def _validate_state(state: Mapping[str, Any], semantic: Mapping[str, Any]) -> None:
    if state["metric_id"] not in semantic["metric_ids"]:
        raise ValueError(f"unknown metric_id: {state['metric_id']}")
    if state["baseline"] not in semantic["periods"]:
        raise ValueError(f"unknown baseline period: {state['baseline']}")
    if state["focus"] not in semantic["periods"]:
        raise ValueError(f"unknown focus period: {state['focus']}")
    if state["baseline"] == state["focus"]:
        raise ValueError("baseline and focus periods must differ")


def _validate_intent(intent: Mapping[str, Any], semantic: Mapping[str, Any]) -> None:
    if intent.get("semantic_version") != semantic["version"]:
        raise ValueError("semantic version mismatch")
    if intent.get("metric_id") not in semantic["metric_ids"]:
        raise ValueError(f"unknown metric_id: {intent.get('metric_id')}")
    if intent.get("baseline") not in semantic["periods"]:
        raise ValueError(f"unknown baseline period: {intent.get('baseline')}")
    if intent.get("focus") not in semantic["periods"]:
        raise ValueError(f"unknown focus period: {intent.get('focus')}")

    action = intent.get("action")
    if action not in {"compare_periods", "breakdown_delta"}:
        raise ValueError(f"unknown action: {action}")

    filters = intent.get("filters", {})
    if not isinstance(filters, Mapping):
        raise ValueError("filters must be a mapping")
    unknown_filters = set(filters) - set(semantic["dimension_ids"])
    if unknown_filters:
        raise ValueError(f"unknown filter dimensions: {sorted(unknown_filters)}")

    group_by = intent.get("group_by")
    if action == "compare_periods" and group_by is not None:
        raise ValueError("compare_periods must not contain group_by")
    if action == "breakdown_delta":
        if group_by not in semantic["dimension_ids"]:
            raise ValueError(f"unknown group_by dimension: {group_by}")
        if group_by in filters:
            raise ValueError("group_by dimension is already fixed by filters")


def _matches_filters(row: Mapping[str, Any], filters: Mapping[str, Any]) -> bool:
    return all(row.get(key) == value for key, value in filters.items())


def execute_intent(
    intent: Mapping[str, Any],
    facts: Sequence[Mapping[str, Any]] = DEMO_FACTS,
    semantic: Mapping[str, Any] = SEMANTIC,
) -> dict[str, Any]:
    """Исполняет только разрешённый intent над проверенными учебными фактами."""
    _validate_intent(intent, semantic)

    metric_id = intent["metric_id"]
    baseline = intent["baseline"]
    focus = intent["focus"]
    filters = intent.get("filters", {})
    selected = [row for row in facts if _matches_filters(row, filters)]

    baseline_value = sum(
        float(row[metric_id]) for row in selected if row["quarter"] == baseline
    )
    focus_value = sum(
        float(row[metric_id]) for row in selected if row["quarter"] == focus
    )
    base = {
        "metric_id": metric_id,
        "baseline": baseline,
        "focus": focus,
        "baseline_value": baseline_value,
        "focus_value": focus_value,
        "delta": focus_value - baseline_value,
        "unit": semantic["metric_ids"][metric_id]["unit"],
        "filters": dict(filters),
        "semantic_version": semantic["version"],
    }

    if intent["action"] == "compare_periods":
        return {"kind": "period_comparison", **base}

    group_by = intent["group_by"]
    segment_names = sorted({str(row[group_by]) for row in selected})
    segments = []
    for segment in segment_names:
        segment_rows = [row for row in selected if str(row[group_by]) == segment]
        segment_baseline = sum(
            float(row[metric_id])
            for row in segment_rows
            if row["quarter"] == baseline
        )
        segment_focus = sum(
            float(row[metric_id])
            for row in segment_rows
            if row["quarter"] == focus
        )
        segments.append(
            {
                "segment": segment,
                "baseline_value": segment_baseline,
                "focus_value": segment_focus,
                "delta": segment_focus - segment_baseline,
            }
        )

    return {
        "kind": "delta_breakdown",
        "group_by": group_by,
        "segments": segments,
        **base,
    }


def _intent(
    state: Mapping[str, Any],
    action: str,
    *,
    group_by: str | None = None,
    filters: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "action": action,
        "metric_id": state["metric_id"],
        "baseline": state["baseline"],
        "focus": state["focus"],
        "group_by": group_by,
        "filters": dict(filters or {}),
        "semantic_version": state["semantic_version"],
    }


def _stop(status: str, reason: str) -> dict[str, Any]:
    return {"kind": "stop", "status": status, "reason": reason}


def choose_next_action(
    state: Mapping[str, Any],
    trace: Sequence[Mapping[str, Any]],
    semantic: Mapping[str, Any] = SEMANTIC,
) -> dict[str, Any]:
    """Возвращает следующий разрешённый intent либо явное решение stop."""
    if not trace:
        return {
            "kind": "intent",
            "intent": _intent(state, "compare_periods"),
            "reason": "Сначала проверяем, существовало ли падение.",
        }

    observation = trace[-1]["observation"]
    if observation.get("semantic_version") != state["semantic_version"]:
        return _stop(
            "semantic_version_mismatch",
            "Наблюдение получено не по той версии semantic contract.",
        )

    if observation["kind"] == "period_comparison":
        if observation["delta"] >= 0:
            return _stop(
                "premise_not_supported",
                "В фокусном периоде метрика не снизилась; исходная посылка не подтверждена.",
            )
        first_dimension = next(
            (
                dimension
                for dimension in semantic["investigation_order"]
                if dimension in semantic["dimension_ids"]
            ),
            None,
        )
        if first_dimension is None:
            return _stop(
                "needs_clarification",
                "В semantic contract нет разрешённого измерения для следующего шага.",
            )
        return {
            "kind": "intent",
            "intent": _intent(
                state,
                "breakdown_delta",
                group_by=first_dimension,
            ),
            "reason": "Падение подтверждено; ищем вклад сегментов.",
        }

    if observation["kind"] != "delta_breakdown":
        return _stop("unsupported_observation", "Policy не знает такой тип наблюдения.")

    segments = observation["segments"]
    if not segments:
        return _stop(
            "insufficient_data",
            "Исполнитель не вернул сегменты для продолжения расследования.",
        )

    segment_delta = sum(float(item["delta"]) for item in segments)
    if round(segment_delta, 6) != round(float(observation["delta"]), 6):
        return _stop(
            "observation_mismatch",
            "Сумма вкладов сегментов не совпадает с изменением текущего среза.",
        )

    worst = min(segments, key=lambda item: float(item["delta"]))
    if worst["delta"] >= 0:
        return _stop(
            "inconclusive",
            "Отрицательный вклад не локализован в доступных сегментах.",
        )

    used_dimensions = {
        item["intent"]["group_by"]
        for item in trace
        if item["intent"].get("group_by") is not None
    }
    current_filters = dict(trace[-1]["intent"].get("filters", {}))
    current_filters[observation["group_by"]] = worst["segment"]
    next_dimension = next(
        (
            dimension
            for dimension in semantic["investigation_order"]
            if dimension in semantic["dimension_ids"]
            and dimension not in used_dimensions
            and dimension not in current_filters
        ),
        None,
    )
    if next_dimension is None:
        return _stop(
            "ready_for_review",
            "Все разрешённые уровни детализации пройдены; пора проверить вывод.",
        )

    return {
        "kind": "intent",
        "intent": _intent(
            state,
            "breakdown_delta",
            group_by=next_dimension,
            filters=current_filters,
        ),
        "reason": (
            f"Наибольший отрицательный вклад даёт сегмент {worst['segment']}; "
            f"детализируем по {next_dimension}."
        ),
    }


def _build_finding(
    state: Mapping[str, Any], trace: Sequence[Mapping[str, Any]]
) -> dict[str, Any] | None:
    if not trace or trace[0]["observation"]["kind"] != "period_comparison":
        return None

    path = []
    for item in trace[1:]:
        observation = item["observation"]
        if observation["kind"] != "delta_breakdown" or not observation["segments"]:
            continue
        worst = min(observation["segments"], key=lambda row: float(row["delta"]))
        path.append(
            {
                "dimension": observation["group_by"],
                "segment": worst["segment"],
                "delta": worst["delta"],
            }
        )

    return {
        "metric_id": state["metric_id"],
        "total_delta": trace[0]["observation"]["delta"],
        "path": path,
        "statement": (
            "Trace локализует наибольший отрицательный вклад, "
            "но сам по себе не доказывает причину изменения."
        ),
    }


def investigate(
    question: str,
    *,
    metric_id: str = "paid_revenue",
    baseline: str = "Q1",
    focus: str = "Q2",
    max_steps: int = 3,
    semantic: Mapping[str, Any] = SEMANTIC,
    executor: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Запускает цикл policy → intent → executor → observation до явного stop."""
    if not isinstance(max_steps, int) or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")

    state = {
        "question": question,
        "metric_id": metric_id,
        "baseline": baseline,
        "focus": focus,
        "semantic_version": semantic["version"],
    }
    _validate_state(state, semantic)
    run = executor or (lambda intent: execute_intent(intent, semantic=semantic))
    trace: list[dict[str, Any]] = []

    while True:
        decision = choose_next_action(state, trace, semantic)
        if decision["kind"] == "stop":
            return {
                "status": decision["status"],
                "reason": decision["reason"],
                "state": state,
                "trace": trace,
                "finding": (
                    _build_finding(state, trace)
                    if decision["status"] == "ready_for_review"
                    else None
                ),
            }

        if len(trace) >= max_steps:
            return {
                "status": "step_budget_exhausted",
                "reason": "Лимит шагов исчерпан до следующего запроса.",
                "state": state,
                "trace": trace,
                "finding": None,
            }

        intent = decision["intent"]
        try:
            observation = dict(run(intent))
        except (KeyError, TypeError, ValueError) as error:
            return {
                "status": "executor_error",
                "reason": str(error),
                "state": state,
                "trace": trace,
                "finding": None,
            }
        trace.append(
            {
                "intent": intent,
                "policy_reason": decision["reason"],
                "observation": observation,
            }
        )


if __name__ == "__main__":
    result = investigate("Почему paid_revenue снизилась в Q2 относительно Q1?")
    print(json.dumps(result, ensure_ascii=False, indent=2))
