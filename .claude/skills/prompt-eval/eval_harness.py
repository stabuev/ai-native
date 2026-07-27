"""Offline eval core for lesson 2.5.

The harness knows nothing about a specific model provider. ``run_case`` is the
boundary: in the lesson it returns recorded outputs, while a live adapter may call
one chosen API. The evaluation logic remains deterministic and testable.
"""

from collections import defaultdict
import json
import math


REQUIRED_CASE_FIELDS = {"id", "input", "expected", "slice"}

DEMO_CASES = [
    {
        "id": "billing-double-charge",
        "input": "Списали оплату дважды за один месяц.",
        "expected": "billing",
        "slice": "regular",
    },
    {
        "id": "billing-after-cancellation",
        "input": "Отменил подписку, но сегодня деньги списали снова.",
        "expected": "billing",
        "slice": "regular",
    },
    {
        "id": "access-password",
        "input": "После смены пароля не могу войти в аккаунт.",
        "expected": "access",
        "slice": "critical",
    },
    {
        "id": "bug-empty-export",
        "input": "Экспорт CSV завершается, но скачанный файл пустой.",
        "expected": "bug",
        "slice": "regular",
    },
    {
        "id": "access-after-payment",
        "input": "Оплата прошла, но после продления аккаунт всё равно заблокирован.",
        "expected": "access",
        "slice": "critical",
    },
]

DEMO_PROMPTS = {
    "baseline": (
        "Определи главную проблему пользователя. Верни одну метку: "
        "billing, access, bug или other.\nСообщение:\n{input}"
    ),
    "candidate": (
        "Определи главную проблему пользователя. Верни одну метку: "
        "billing, access, bug или other.\n"
        "Если в сообщении упомянуты оплата или подписка, выбери billing.\n"
        "Сообщение:\n{input}"
    ),
}

# These responses are recorded fixtures, not live model calls. They make Build It
# reproducible and keep the lesson usable without an API key.
DEMO_OUTPUTS = {
    "baseline": {
        "billing-double-charge": "other",
        "billing-after-cancellation": "other",
        "access-password": "access",
        "bug-empty-export": "bug",
        "access-after-payment": "access",
    },
    "candidate": {
        "billing-double-charge": "billing",
        "billing-after-cancellation": "billing",
        "access-password": "access",
        "bug-empty-export": "bug",
        "access-after-payment": "billing",
    },
}


def exact_label(pred, expected):
    """Return 1.0 only for the same normalized label."""
    if not isinstance(pred, str) or not isinstance(expected, str):
        return 0.0
    return 1.0 if pred.strip().casefold() == expected.strip().casefold() else 0.0


def naive_contains(pred, expected):
    """A deliberately weak grader used to demonstrate false positives."""
    if not isinstance(pred, str) or not isinstance(expected, str):
        return 0.0
    return 1.0 if expected.casefold() in pred.casefold() else 0.0


def validate_cases(cases):
    """Fail fast when a test set cannot support a meaningful run."""
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a non-empty list")

    seen_ids = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"cases[{index}] must be an object")

        missing = REQUIRED_CASE_FIELDS - set(case)
        if missing:
            fields = ", ".join(sorted(missing))
            raise ValueError(f"cases[{index}] missing fields: {fields}")

        for field in REQUIRED_CASE_FIELDS:
            if not isinstance(case[field], str) or not case[field].strip():
                raise ValueError(f"cases[{index}].{field} must be a non-empty string")

        case_id = case["id"]
        if case_id in seen_ids:
            raise ValueError(f"duplicate case id: {case_id}")
        seen_ids.add(case_id)


def _checked_score(value, case_id):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"grader returned a non-numeric score for {case_id}")
    score = float(value)
    if not math.isfinite(score) or not 0.0 <= score <= 1.0:
        raise ValueError(f"grader score for {case_id} must be between 0 and 1")
    return score


def evaluate(version, cases, run_case, grader=exact_label):
    """Run one version and return overall, slice, and per-case evidence."""
    validate_cases(cases)
    if not callable(run_case) or not callable(grader):
        raise TypeError("run_case and grader must be callable")

    per_case = []
    slice_scores = defaultdict(list)

    for case in cases:
        case_id = case["id"]
        try:
            pred = run_case(version, case)
        except Exception as exc:
            raise RuntimeError(f"runner failed for {version}/{case_id}") from exc

        try:
            raw_score = grader(pred, case["expected"])
        except Exception as exc:
            raise RuntimeError(f"grader failed for {version}/{case_id}") from exc
        score = _checked_score(raw_score, case_id)
        result = {
            "id": case_id,
            "slice": case["slice"],
            "expected": case["expected"],
            "pred": pred,
            "score": score,
        }
        per_case.append(result)
        slice_scores[case["slice"]].append(score)

    by_slice = {}
    for slice_name, scores in sorted(slice_scores.items()):
        by_slice[slice_name] = {
            "score": sum(scores) / len(scores),
            "passed": sum(score == 1.0 for score in scores),
            "total": len(scores),
        }

    return {
        "version": version,
        "score": sum(item["score"] for item in per_case) / len(per_case),
        "passed": sum(item["score"] == 1.0 for item in per_case),
        "total": len(per_case),
        "by_slice": by_slice,
        "per_case": per_case,
    }


def compare_versions(baseline, candidate, cases, run_case, grader=exact_label):
    """Compare the same cases and grader, preserving paired evidence."""
    baseline_report = evaluate(baseline, cases, run_case, grader)
    candidate_report = evaluate(candidate, cases, run_case, grader)

    baseline_by_id = {item["id"]: item for item in baseline_report["per_case"]}
    candidate_by_id = {item["id"]: item for item in candidate_report["per_case"]}

    regressions = []
    improvements = []
    for case in cases:
        case_id = case["id"]
        old_score = baseline_by_id[case_id]["score"]
        new_score = candidate_by_id[case_id]["score"]
        if new_score < old_score:
            regressions.append(case_id)
        elif new_score > old_score:
            improvements.append(case_id)

    slice_deltas = {}
    for slice_name in baseline_report["by_slice"]:
        old_score = baseline_report["by_slice"][slice_name]["score"]
        new_score = candidate_report["by_slice"][slice_name]["score"]
        slice_deltas[slice_name] = round(new_score - old_score, 12)

    return {
        "baseline": baseline_report,
        "candidate": candidate_report,
        "delta": round(candidate_report["score"] - baseline_report["score"], 12),
        "slice_deltas": slice_deltas,
        "regressions": regressions,
        "improvements": improvements,
    }


def release_decision(comparison, protected_slices=()):
    """Apply a small, explicit release gate to a completed comparison."""
    reject_reasons = []
    review_reasons = []

    if comparison["delta"] < 0:
        reject_reasons.append(
            f"overall score regressed by {comparison['delta']:.3f}"
        )

    for slice_name in protected_slices:
        if slice_name not in comparison["slice_deltas"]:
            review_reasons.append(f"protected slice {slice_name!r} has no cases")
            continue
        slice_delta = comparison["slice_deltas"][slice_name]
        if slice_delta < 0:
            reject_reasons.append(
                f"protected slice {slice_name!r} regressed by {slice_delta:.3f}"
            )

    if reject_reasons:
        return {
            "decision": "reject",
            "reasons": reject_reasons + review_reasons,
        }
    if comparison["delta"] <= 0:
        review_reasons.append("candidate has no measured overall improvement")
    if comparison["regressions"]:
        review_reasons.append(
            "candidate has case-level regressions: "
            + ", ".join(comparison["regressions"])
        )
    if review_reasons:
        return {"decision": "review", "reasons": review_reasons}
    return {
        "decision": "accept",
        "reasons": ["overall score improved without observed regressions"],
    }


def recorded_runner(version, case):
    """Return the stored response for the demo version and case."""
    return DEMO_OUTPUTS[version][case["id"]]


if __name__ == "__main__":
    comparison = compare_versions(
        "baseline",
        "candidate",
        DEMO_CASES,
        recorded_runner,
    )
    decision = release_decision(comparison, protected_slices=("critical",))
    print(json.dumps({"comparison": comparison, "decision": decision},
                     ensure_ascii=False, indent=2))
