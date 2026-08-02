"""Детерминированный quality gate для аналитического отчёта урока 5.5.

Сначала сохранённый результат BI-расследования 5.4 преобразуется в validation packet.
Затем gate возвращает результаты проверок, сигнал аномалии, решение
publish/review/block и проверяемый Markdown-отчёт. Только стандартная библиотека Python.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from statistics import mean, pstdev
from typing import Any


DEMO_POLICY = {
    "semantic_version": "1.1",
    "metric_id": "paid_revenue",
    "required_filters": {"status": "paid"},
    "baseline": "Q1",
    "focus": "Q2",
    "expected_focus_value": 200.0,
    "expected_segments": {
        "region": ["Москва", "Питер", "Казань"],
        "product|region=Питер": ["Basic", "Pro"],
    },
    "minimum_baseline_points": 5,
    "anomaly_z_threshold": 2.0,
}


DEMO_PACKET = {
    "run_id": "phase-5-paid-revenue-q2",
    "as_of": "2026-07-01",
    "trace_status": "ready_for_review",
    "semantic_version": "1.1",
    "metric_id": "paid_revenue",
    "unit": "RUB",
    "baseline": "Q1",
    "focus": "Q2",
    "filters": {"status": "paid"},
    "totals": {"Q1": 270.0, "Q2": 200.0},
    "breakdowns": {
        "region": [
            {
                "segment": "Москва",
                "baseline_value": 170.0,
                "focus_value": 150.0,
                "delta": -20.0,
            },
            {
                "segment": "Питер",
                "baseline_value": 80.0,
                "focus_value": 30.0,
                "delta": -50.0,
            },
            {
                "segment": "Казань",
                "baseline_value": 20.0,
                "focus_value": 20.0,
                "delta": 0.0,
            },
        ],
        "product|region=Питер": [
            {
                "segment": "Basic",
                "baseline_value": 30.0,
                "focus_value": 20.0,
                "delta": -10.0,
            },
            {
                "segment": "Pro",
                "baseline_value": 50.0,
                "focus_value": 10.0,
                "delta": -40.0,
            },
        ],
    },
    "evidence_path": [
        {
            "breakdown_id": "region",
            "dimension": "region",
            "segment": "Питер",
            "delta": -50.0,
        },
        {
            "breakdown_id": "product|region=Питер",
            "dimension": "product",
            "segment": "Pro",
            "delta": -40.0,
        },
    ],
    # Пять прошлых сопоставимых периодов + текущий период последним.
    "history": [
        {"period": "2025-Q1", "value": 198.0},
        {"period": "2025-Q2", "value": 203.0},
        {"period": "2025-Q3", "value": 201.0},
        {"period": "2025-Q4", "value": 197.0},
        {"period": "2026-Q1", "value": 202.0},
        {"period": "2026-Q2", "value": 200.0},
    ],
}


# Сохранённый результат investigate() из 5.4. Он намеренно имеет другую форму:
# задача адаптера — сделать границу между trace и validation packet наблюдаемой.
DEMO_INVESTIGATION = {
    "status": "ready_for_review",
    "state": {
        "question": "Почему paid_revenue снизилась в Q2 относительно Q1?",
        "metric_id": "paid_revenue",
        "baseline": "Q1",
        "focus": "Q2",
        "semantic_version": "1.1",
    },
    "trace": [
        {
            "observation": {
                "kind": "period_comparison",
                "metric_id": "paid_revenue",
                "baseline": "Q1",
                "focus": "Q2",
                "baseline_value": 270.0,
                "focus_value": 200.0,
                "delta": -70.0,
                "unit": "RUB",
                "filters": {},
                "semantic_version": "1.1",
            }
        },
        {
            "observation": {
                "kind": "delta_breakdown",
                "group_by": "region",
                "segments": [
                    {
                        "segment": "Москва",
                        "baseline_value": 170.0,
                        "focus_value": 150.0,
                        "delta": -20.0,
                    },
                    {
                        "segment": "Питер",
                        "baseline_value": 80.0,
                        "focus_value": 30.0,
                        "delta": -50.0,
                    },
                    {
                        "segment": "Казань",
                        "baseline_value": 20.0,
                        "focus_value": 20.0,
                        "delta": 0.0,
                    },
                ],
                "metric_id": "paid_revenue",
                "baseline": "Q1",
                "focus": "Q2",
                "baseline_value": 270.0,
                "focus_value": 200.0,
                "delta": -70.0,
                "unit": "RUB",
                "filters": {},
                "semantic_version": "1.1",
            }
        },
        {
            "observation": {
                "kind": "delta_breakdown",
                "group_by": "product",
                "segments": [
                    {
                        "segment": "Basic",
                        "baseline_value": 30.0,
                        "focus_value": 20.0,
                        "delta": -10.0,
                    },
                    {
                        "segment": "Pro",
                        "baseline_value": 50.0,
                        "focus_value": 10.0,
                        "delta": -40.0,
                    },
                ],
                "metric_id": "paid_revenue",
                "baseline": "Q1",
                "focus": "Q2",
                "baseline_value": 80.0,
                "focus_value": 30.0,
                "delta": -50.0,
                "unit": "RUB",
                "filters": {"region": "Питер"},
                "semantic_version": "1.1",
            }
        },
    ],
    "finding": {
        "metric_id": "paid_revenue",
        "total_delta": -70.0,
        "path": [
            {"dimension": "region", "segment": "Питер", "delta": -50.0},
            {"dimension": "product", "segment": "Pro", "delta": -40.0},
        ],
    },
}


DEMO_SEMANTIC = {
    "version": "1.1",
    "metric_ids": {
        "paid_revenue": {
            "unit": "RUB",
            "required_filter": {"status": "paid"},
        }
    },
}


def _is_finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _same_number(left: Any, right: Any) -> bool:
    return _is_finite_number(left) and _is_finite_number(right) and math.isclose(
        float(left), float(right), rel_tol=0.0, abs_tol=1e-9
    )


def _check(
    check_id: str,
    passed: bool,
    message: str,
    *,
    evidence: Any = None,
) -> dict[str, Any]:
    """Создаёт трассируемый результат жёсткой проверки."""
    return {
        "id": check_id,
        "passed": bool(passed),
        "failure_effect": "block",
        "message": message,
        "evidence": evidence,
    }


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    return value


def _breakdown_id(group_by: str, filters: Mapping[str, Any]) -> str:
    if not filters:
        return group_by
    suffix = ",".join(f"{key}={filters[key]}" for key in sorted(filters))
    return f"{group_by}|{suffix}"


def build_validation_packet(
    investigation: Mapping[str, Any],
    semantic: Mapping[str, Any],
    *,
    run_id: str,
    as_of: str,
    history: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Преобразует сохранённый результат 5.4 во вход quality gate 5.5.

    Trace даёт наблюдения и evidence path. Semantic contract даёт единицу и
    обязательные фильтры. Run metadata и сопоставимая история приходят отдельно:
    адаптер не должен придумывать их из финальной фразы расследования.
    """
    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError("run_id must be a non-empty string")
    if not isinstance(as_of, str) or not as_of.strip():
        raise ValueError("as_of must be a non-empty string")
    if not isinstance(history, Sequence) or isinstance(history, (str, bytes)):
        raise ValueError("history must be a sequence of points")

    investigation = _require_mapping(investigation, "investigation")
    semantic = _require_mapping(semantic, "semantic")
    state = _require_mapping(investigation.get("state"), "investigation.state")
    trace = investigation.get("trace")
    if not isinstance(trace, Sequence) or isinstance(trace, (str, bytes)):
        raise ValueError("investigation.trace must be a sequence")

    metric_id = state.get("metric_id")
    metric_ids = _require_mapping(semantic.get("metric_ids"), "semantic.metric_ids")
    metric_contract = _require_mapping(
        metric_ids.get(metric_id), f"semantic.metric_ids.{metric_id}"
    )
    semantic_version = state.get("semantic_version")
    if semantic_version != semantic.get("version"):
        raise ValueError("investigation and semantic contract versions differ")

    baseline = state.get("baseline")
    focus = state.get("focus")
    if not all(isinstance(value, str) and value for value in (baseline, focus)):
        raise ValueError("baseline and focus must be non-empty strings")

    required_filters = metric_contract.get(
        "required_filters", metric_contract.get("required_filter", {})
    )
    required_filters = _require_mapping(
        required_filters, f"semantic.metric_ids.{metric_id}.required_filter"
    )

    totals: dict[str, Any] = {}
    breakdowns: dict[str, list[dict[str, Any]]] = {}
    unit = metric_contract.get("unit")

    for index, step in enumerate(trace):
        step = _require_mapping(step, f"investigation.trace[{index}]")
        observation = _require_mapping(
            step.get("observation"), f"investigation.trace[{index}].observation"
        )
        if observation.get("semantic_version") != semantic_version:
            raise ValueError(f"trace observation {index} has another semantic version")
        if observation.get("metric_id") != metric_id:
            raise ValueError(f"trace observation {index} has another metric ID")
        if observation.get("baseline") != baseline or observation.get("focus") != focus:
            raise ValueError(f"trace observation {index} has other periods")

        kind = observation.get("kind")
        if kind == "period_comparison":
            totals = {
                baseline: observation.get("baseline_value"),
                focus: observation.get("focus_value"),
            }
            unit = observation.get("unit", unit)
        elif kind == "delta_breakdown":
            group_by = observation.get("group_by")
            filters = _require_mapping(
                observation.get("filters", {}),
                f"investigation.trace[{index}].observation.filters",
            )
            rows = observation.get("segments")
            if not isinstance(group_by, str) or not group_by:
                raise ValueError(f"trace observation {index} has no group_by")
            if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
                raise ValueError(f"trace observation {index} has invalid segments")
            breakdowns[_breakdown_id(group_by, filters)] = [
                dict(_require_mapping(row, f"trace segment {row_index}"))
                for row_index, row in enumerate(rows)
            ]
        else:
            raise ValueError(f"trace observation {index} has unknown kind: {kind}")

    finding = investigation.get("finding")
    path = finding.get("path", []) if isinstance(finding, Mapping) else []
    if not isinstance(path, Sequence) or isinstance(path, (str, bytes)):
        raise ValueError("investigation.finding.path must be a sequence")

    evidence_path: list[dict[str, Any]] = []
    for index, hop in enumerate(path):
        hop = _require_mapping(hop, f"investigation.finding.path[{index}]")
        dimension = hop.get("dimension")
        segment = hop.get("segment")
        delta = hop.get("delta")
        candidates = []
        for breakdown_id, rows in breakdowns.items():
            if breakdown_id.split("|", 1)[0] != dimension:
                continue
            if any(
                row.get("segment") == segment and _same_number(row.get("delta"), delta)
                for row in rows
            ):
                candidates.append(breakdown_id)
        if len(candidates) != 1:
            raise ValueError(f"evidence hop {index} has no unique supporting breakdown")
        evidence_path.append(
            {
                "breakdown_id": candidates[0],
                "dimension": dimension,
                "segment": segment,
                "delta": delta,
            }
        )

    return {
        "run_id": run_id,
        "as_of": as_of,
        "trace_status": investigation.get("status"),
        "semantic_version": semantic_version,
        "metric_id": metric_id,
        "unit": unit,
        "baseline": baseline,
        "focus": focus,
        "filters": dict(required_filters),
        "totals": totals,
        "breakdowns": breakdowns,
        "evidence_path": evidence_path,
        "history": [dict(_require_mapping(point, "history point")) for point in history],
    }


def _breakdown_checks(
    breakdown_id: str,
    rows: Any,
    expected_segments: Sequence[str],
    parent_delta: Any,
) -> list[dict[str, Any]]:
    """Проверяет полноту строк, арифметику каждой строки и сумму вкладов."""
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return [
            _check(
                f"{breakdown_id}.shape",
                False,
                f"Декомпозиция {breakdown_id} должна быть списком строк.",
                evidence=rows,
            )
        ]

    row_mappings = [row for row in rows if isinstance(row, Mapping)]
    actual_segments = [str(row.get("segment")) for row in row_mappings]
    expected_set = set(expected_segments)
    actual_set = set(actual_segments)
    completeness_ok = (
        len(row_mappings) == len(rows)
        and len(actual_segments) == len(actual_set)
        and actual_set == expected_set
    )
    checks = [
        _check(
            f"{breakdown_id}.segments",
            completeness_ok,
            (
                f"Сегменты {breakdown_id} полны и не дублируются."
                if completeness_ok
                else f"Сегменты {breakdown_id} не совпадают с контрактом."
            ),
            evidence={
                "expected": list(expected_segments),
                "actual": actual_segments,
            },
        )
    ]

    row_arithmetic_ok = len(row_mappings) == len(rows)
    deltas: list[float] = []
    for row in row_mappings:
        baseline_value = row.get("baseline_value")
        focus_value = row.get("focus_value")
        delta = row.get("delta")
        valid_numbers = all(
            _is_finite_number(value)
            for value in (baseline_value, focus_value, delta)
        )
        if not valid_numbers:
            row_arithmetic_ok = False
            continue
        expected_delta = float(focus_value) - float(baseline_value)
        if not _same_number(delta, expected_delta):
            row_arithmetic_ok = False
        deltas.append(float(delta))

    checks.append(
        _check(
            f"{breakdown_id}.row_arithmetic",
            row_arithmetic_ok,
            (
                f"Delta каждой строки {breakdown_id} равна focus − baseline."
                if row_arithmetic_ok
                else f"В строках {breakdown_id} есть нечисловое значение или неверная delta."
            ),
        )
    )

    reconciliation_ok = (
        row_arithmetic_ok
        and len(deltas) == len(rows)
        and _same_number(sum(deltas), parent_delta)
    )
    checks.append(
        _check(
            f"{breakdown_id}.reconciliation",
            reconciliation_ok,
            (
                f"Вклады {breakdown_id} сходятся с родительским изменением."
                if reconciliation_ok
                else f"Сумма вкладов {breakdown_id} не равна родительскому изменению."
            ),
            evidence={
                "sum_of_deltas": sum(deltas) if deltas else None,
                "parent_delta": parent_delta,
            },
        )
    )
    return checks


def _evidence_path_is_supported(packet: Mapping[str, Any]) -> tuple[bool, list[str]]:
    breakdowns = packet.get("breakdowns", {})
    path = packet.get("evidence_path", [])
    if not isinstance(breakdowns, Mapping) or not isinstance(path, Sequence):
        return False, []
    if not path:
        return False, ["путь доказательств пуст"]

    unsupported: list[str] = []
    for step in path:
        if not isinstance(step, Mapping):
            unsupported.append("неструктурированный шаг")
            continue
        breakdown_id = step.get("breakdown_id")
        rows = breakdowns.get(breakdown_id, [])
        matched = any(
            isinstance(row, Mapping)
            and row.get("segment") == step.get("segment")
            and _same_number(row.get("delta"), step.get("delta"))
            for row in rows
        )
        if not matched:
            unsupported.append(
                f"{breakdown_id}:{step.get('segment')}:{step.get('delta')}"
            )
    return not unsupported, unsupported


def validate_packet(
    packet: Mapping[str, Any], policy: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Проверяет контракт, числа, полноту и сверки пакета 5.4."""
    required_fields = {
        "run_id",
        "as_of",
        "trace_status",
        "semantic_version",
        "metric_id",
        "unit",
        "baseline",
        "focus",
        "filters",
        "totals",
        "breakdowns",
        "evidence_path",
        "history",
    }
    missing = sorted(required_fields - set(packet))
    checks = [
        _check(
            "packet.required_fields",
            not missing,
            (
                "Все обязательные поля пакета присутствуют."
                if not missing
                else f"В пакете отсутствуют поля: {', '.join(missing)}."
            ),
            evidence={"missing": missing},
        )
    ]
    if missing:
        return checks

    checks.extend(
        [
            _check(
                "trace.ready_for_review",
                packet.get("trace_status") == "ready_for_review",
                "Trace завершён статусом ready_for_review."
                if packet.get("trace_status") == "ready_for_review"
                else "Trace ещё не готов к выпускной проверке.",
                evidence=packet.get("trace_status"),
            ),
            _check(
                "contract.semantic_version",
                packet.get("semantic_version") == policy.get("semantic_version"),
                "Версия semantic contract совпадает с политикой выпуска."
                if packet.get("semantic_version") == policy.get("semantic_version")
                else "Версия semantic contract не совпадает с политикой выпуска.",
                evidence={
                    "expected": policy.get("semantic_version"),
                    "actual": packet.get("semantic_version"),
                },
            ),
            _check(
                "contract.metric",
                packet.get("metric_id") == policy.get("metric_id"),
                "Metric ID совпадает с политикой выпуска."
                if packet.get("metric_id") == policy.get("metric_id")
                else "Пакет содержит другую метрику.",
                evidence={
                    "expected": policy.get("metric_id"),
                    "actual": packet.get("metric_id"),
                },
            ),
            _check(
                "contract.periods",
                packet.get("baseline") == policy.get("baseline")
                and packet.get("focus") == policy.get("focus"),
                "Периоды совпадают с политикой выпуска."
                if packet.get("baseline") == policy.get("baseline")
                and packet.get("focus") == policy.get("focus")
                else "Периоды пакета не совпадают с политикой выпуска.",
                evidence={
                    "expected": [policy.get("baseline"), policy.get("focus")],
                    "actual": [packet.get("baseline"), packet.get("focus")],
                },
            ),
            _check(
                "contract.required_filters",
                packet.get("filters") == policy.get("required_filters"),
                "Обязательные фильтры применены."
                if packet.get("filters") == policy.get("required_filters")
                else "Обязательные фильтры отсутствуют или изменены.",
                evidence={
                    "expected": policy.get("required_filters"),
                    "actual": packet.get("filters"),
                },
            ),
        ]
    )

    totals = packet.get("totals")
    totals_are_mapping = isinstance(totals, Mapping)
    baseline_value = totals.get(packet.get("baseline")) if totals_are_mapping else None
    focus_value = totals.get(packet.get("focus")) if totals_are_mapping else None
    totals_are_finite = _is_finite_number(baseline_value) and _is_finite_number(
        focus_value
    )
    checks.append(
        _check(
            "totals.finite",
            totals_are_finite,
            "Итоги baseline и focus — конечные числа."
            if totals_are_finite
            else "Итоги отсутствуют, имеют неверный тип, NaN или бесконечность.",
            evidence={"baseline": baseline_value, "focus": focus_value},
        )
    )
    checks.append(
        _check(
            "totals.focus_control",
            _same_number(focus_value, policy.get("expected_focus_value")),
            "Итог фокусного периода совпадает с контрольным значением."
            if _same_number(focus_value, policy.get("expected_focus_value"))
            else "Итог фокусного периода не совпадает с контрольным значением.",
            evidence={
                "expected": policy.get("expected_focus_value"),
                "actual": focus_value,
            },
        )
    )

    total_delta = (
        float(focus_value) - float(baseline_value) if totals_are_finite else None
    )
    breakdowns = packet.get("breakdowns")
    breakdowns_mapping = breakdowns if isinstance(breakdowns, Mapping) else {}
    expected_segments = policy.get("expected_segments", {})
    region_rows = breakdowns_mapping.get("region")
    checks.extend(
        _breakdown_checks(
            "region",
            region_rows,
            expected_segments.get("region", []),
            total_delta,
        )
    )

    piter_delta = None
    if isinstance(region_rows, Sequence):
        for row in region_rows:
            if isinstance(row, Mapping) and row.get("segment") == "Питер":
                piter_delta = row.get("delta")
                break
    product_id = "product|region=Питер"
    checks.extend(
        _breakdown_checks(
            product_id,
            breakdowns_mapping.get(product_id),
            expected_segments.get(product_id, []),
            piter_delta,
        )
    )

    evidence_ok, unsupported = _evidence_path_is_supported(packet)
    checks.append(
        _check(
            "evidence_path.supported",
            evidence_ok,
            "Каждый шаг evidence path подтверждён строкой декомпозиции."
            if evidence_ok
            else "Evidence path содержит неподтверждённый или пустой шаг.",
            evidence={"unsupported": unsupported},
        )
    )

    history = packet.get("history")
    history_is_sequence = isinstance(history, Sequence) and not isinstance(
        history, (str, bytes)
    )
    current_history_value = None
    if history_is_sequence and history and isinstance(history[-1], Mapping):
        current_history_value = history[-1].get("value")
    checks.append(
        _check(
            "history.current_matches_focus",
            _same_number(current_history_value, focus_value),
            "Последняя историческая точка совпадает с итогом focus."
            if _same_number(current_history_value, focus_value)
            else "Последняя историческая точка не совпадает с итогом focus.",
            evidence={"history": current_history_value, "focus": focus_value},
        )
    )
    return checks


def detect_current_anomaly(
    history: Any,
    *,
    minimum_baseline_points: int = 5,
    z_threshold: float = 2.0,
) -> dict[str, Any]:
    """Сравнивает последнюю точку с предыдущей историей, не включая её в baseline."""
    if (
        not isinstance(history, Sequence)
        or isinstance(history, (str, bytes))
        or not history
    ):
        return {
            "status": "invalid",
            "message": "История отсутствует или имеет неверный формат.",
        }

    values: list[float] = []
    periods: list[str] = []
    for point in history:
        if not isinstance(point, Mapping) or not _is_finite_number(point.get("value")):
            return {
                "status": "invalid",
                "message": "История содержит нечисловую, NaN или бесконечную точку.",
            }
        periods.append(str(point.get("period", "без периода")))
        values.append(float(point["value"]))

    baseline = values[:-1]
    current = values[-1]
    current_period = periods[-1]
    if len(baseline) < minimum_baseline_points:
        return {
            "status": "insufficient_history",
            "message": "Истории недостаточно, поэтому отсутствие аномалии не доказано.",
            "baseline_points": len(baseline),
            "required_baseline_points": minimum_baseline_points,
            "current": {"period": current_period, "value": current},
        }

    baseline_mean = mean(baseline)
    baseline_sigma = pstdev(baseline)
    if baseline_sigma == 0:
        changed = not _same_number(current, baseline_mean)
        return {
            "status": "review" if changed else "clear",
            "message": (
                "Текущая точка отличается от постоянного baseline; нужен человек."
                if changed
                else "Текущая точка совпадает с постоянным baseline."
            ),
            "baseline_points": len(baseline),
            "baseline_mean": baseline_mean,
            "baseline_sigma": baseline_sigma,
            "z": None,
            "threshold": z_threshold,
            "current": {"period": current_period, "value": current},
        }

    z_value = (current - baseline_mean) / baseline_sigma
    is_anomaly = abs(z_value) > z_threshold
    return {
        "status": "review" if is_anomaly else "clear",
        "message": (
            "Текущая точка статистически необычна; это сигнал для ревью, а не доказанная ошибка."
            if is_anomaly
            else "Текущая точка не пересекает заданный порог аномалии."
        ),
        "baseline_points": len(baseline),
        "baseline_mean": round(baseline_mean, 2),
        "baseline_sigma": round(baseline_sigma, 2),
        "z": round(z_value, 2),
        "threshold": z_threshold,
        "current": {"period": current_period, "value": current},
    }


def decide_release(
    checks: Sequence[Mapping[str, Any]], anomaly: Mapping[str, Any]
) -> str:
    """Возвращает publish, review или block по явной таблице решений."""
    if any(not check.get("passed", False) for check in checks):
        return "block"
    if anomaly.get("status") == "invalid":
        return "block"
    if anomaly.get("status") in {"review", "insufficient_history"}:
        return "review"
    return "publish"


def build_report(
    packet: Mapping[str, Any],
    checks: Sequence[Mapping[str, Any]],
    anomaly: Mapping[str, Any],
    decision: str,
) -> str:
    """Собирает отчёт, не теряя проверки, сигналы и основание решения."""
    totals = packet.get("totals", {})
    baseline = packet.get("baseline", "?")
    focus = packet.get("focus", "?")
    lines = [
        "# Проверенный отчёт по расследованию",
        "",
        f"- Решение: **{decision}**",
        f"- Run ID: `{packet.get('run_id', 'unknown')}`",
        f"- Срез данных: `{packet.get('as_of', 'unknown')}`",
        f"- Metric ID: `{packet.get('metric_id', 'unknown')}`",
        f"- Semantic version: `{packet.get('semantic_version', 'unknown')}`",
        "",
        "## Наблюдаемый результат",
        "",
        f"- {baseline}: {totals.get(baseline, 'нет данных')} {packet.get('unit', '')}",
        f"- {focus}: {totals.get(focus, 'нет данных')} {packet.get('unit', '')}",
    ]
    if _is_finite_number(totals.get(baseline)) and _is_finite_number(totals.get(focus)):
        delta = float(totals[focus]) - float(totals[baseline])
        lines.append(f"- Delta: {delta:g} {packet.get('unit', '')}")

    lines.extend(["", "## Проверки"])
    for check in checks:
        marker = "PASS" if check.get("passed") else "FAIL"
        lines.append(f"- [{marker}] `{check.get('id')}` — {check.get('message')}")

    lines.extend(
        [
            "",
            "## Сигнал аномалии",
            "",
            f"- Статус: `{anomaly.get('status', 'unknown')}`",
            f"- Вывод: {anomaly.get('message', 'нет результата')}",
        ]
    )
    if anomaly.get("z") is not None:
        lines.append(
            f"- z-score: {anomaly['z']} при пороге {anomaly.get('threshold')}"
        )

    lines.extend(["", "## Evidence path"])
    evidence_path = packet.get("evidence_path", [])
    if evidence_path:
        for step in evidence_path:
            lines.append(
                f"- {step.get('dimension')}={step.get('segment')}: "
                f"delta {step.get('delta')} {packet.get('unit', '')}"
            )
    else:
        lines.append("- отсутствует")

    next_action = {
        "publish": "Можно публиковать локализацию изменения с указанной границей доказательств.",
        "review": "Не публиковать автоматически: передать пакет человеку вместе с сигналом.",
        "block": "Не публиковать: исправить пакет или расчёт и повторить все проверки.",
    }[decision]
    lines.extend(
        [
            "",
            "## Следующее действие",
            "",
            next_action,
            "",
            "> Evidence path локализует изменение, но не доказывает его причину.",
        ]
    )
    return "\n".join(lines)


def run_quality_gate(
    packet: Mapping[str, Any], policy: Mapping[str, Any] = DEMO_POLICY
) -> dict[str, Any]:
    """Запускает полный gate и возвращает переносимый пакет решения."""
    checks = validate_packet(packet, policy)
    anomaly = detect_current_anomaly(
        packet.get("history"),
        minimum_baseline_points=int(policy["minimum_baseline_points"]),
        z_threshold=float(policy["anomaly_z_threshold"]),
    )
    decision = decide_release(checks, anomaly)
    report = build_report(packet, checks, anomaly, decision)
    return {
        "run_id": packet.get("run_id"),
        "decision": decision,
        "checks": checks,
        "anomaly": anomaly,
        "report": report,
    }


if __name__ == "__main__":
    packet = build_validation_packet(
        DEMO_INVESTIGATION,
        DEMO_SEMANTIC,
        run_id=DEMO_PACKET["run_id"],
        as_of=DEMO_PACKET["as_of"],
        history=DEMO_PACKET["history"],
    )
    result = run_quality_gate(packet)
    print(json.dumps({k: v for k, v in result.items() if k != "report"}, ensure_ascii=False, indent=2))
    print()
    print(result["report"])
