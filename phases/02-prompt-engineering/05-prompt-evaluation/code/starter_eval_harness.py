"""Starter for the offline eval harness from lesson 2.5.

Copy this file as ``eval_harness.py`` and implement the six marked functions.
The cases, prompts, recorded outputs, runner, and demo call are already provided.
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

# Synthetic recorded responses: they demonstrate the harness mechanics and are
# not evidence about the behavior of a real model.
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
    raise NotImplementedError


def naive_contains(pred, expected):
    """A deliberately weak grader used to demonstrate false positives."""
    raise NotImplementedError


def validate_cases(cases):
    """Fail fast when a test set cannot support a meaningful run."""
    raise NotImplementedError


def evaluate(version, cases, run_case, grader=exact_label):
    """Run one version and return overall, slice, and per-case evidence."""
    raise NotImplementedError


def compare_versions(baseline, candidate, cases, run_case, grader=exact_label):
    """Compare the same cases and grader, preserving paired evidence."""
    raise NotImplementedError


def release_decision(comparison, protected_slices=()):
    """Apply a small, explicit release gate to a completed comparison."""
    raise NotImplementedError


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
