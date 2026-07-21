"""Выбор процесса и спецификация — Build It для урока 12.1.

Без зависимостей. Capstone начинается со спецификации: цель, измеримые метрики
(с baseline и target), ограничения и бюджет. Валидатор проверяет, что спека
полна и метрики реально измеримы — иначе «до/после» в защите не посчитать.
"""
from dataclasses import dataclass, field


@dataclass
class Metric:
    name: str
    baseline: float = None      # «до»
    target: float = None        # цель
    unit: str = ""


@dataclass
class CapstoneSpec:
    goal: str = ""
    metrics: list = field(default_factory=list)
    constraints: list = field(default_factory=list)
    budget_usd: float = None


def is_measurable(metric):
    """Метрика измерима, если заданы и baseline, и target."""
    return metric.baseline is not None and metric.target is not None


def validate_spec(spec):
    """Список проблем спецификации (пустой = готова к сборке)."""
    problems = []
    if not spec.goal.strip():
        problems.append("нет цели")
    if not spec.metrics:
        problems.append("нет метрик")
    elif not any(is_measurable(m) for m in spec.metrics):
        problems.append("ни одна метрика не измерима (нужны baseline и target)")
    if spec.budget_usd is None:
        problems.append("не задан бюджет")
    return problems


if __name__ == "__main__":
    spec = CapstoneSpec(
        goal="Автоматизировать разбор входящих обращений поддержки",
        metrics=[
            Metric("время на обращение", baseline=10.0, target=3.0, unit="мин"),
            Metric("стоимость на обращение", baseline=0.50, target=0.10, unit="$"),
        ],
        constraints=["PII не во внешние модели", "human review на эскалациях"],
        budget_usd=200.0,
    )
    print("Проблемы спеки:", validate_spec(spec) or "нет — готова к сборке")
