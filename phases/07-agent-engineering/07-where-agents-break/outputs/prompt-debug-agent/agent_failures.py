"""Где агенты ломаются: петли, дрейф цели, лимит шагов — Build It для урока 7.4.

Без зависимостей. Воспроизводим типовые поломки агентов и ловим их инженерно:
- петля (агент повторяет одно действие) → детектор повторов;
- дрейф цели (действия перестают относиться к цели) → оценка связи;
- бесконечная работа → лимит шагов.
"""


def detect_loop(actions, repeat=3):
    """Идут ли подряд `repeat` одинаковых действий (петля)."""
    if len(actions) < repeat:
        return False
    tail = actions[-repeat:]
    return all(a == tail[0] for a in tail)


def goal_relatedness(goal, action):
    """Грубая оценка связи действия с целью (доля общих слов). 0..1."""
    g = set(goal.lower().split())
    a = set(str(action).lower().split())
    return len(g & a) / len(a) if a else 0.0


def run_guarded(policy, goal="", max_steps=10, repeat=3, drift_threshold=None):
    """Гонять policy(actions)->action|'DONE', ловя петли, дрейф и лимит шагов.

    Возвращает {status, actions}. status: done | loop_detected | goal_drift | step_limit.
    """
    actions = []
    for _ in range(max_steps):
        action = policy(actions)
        if action == "DONE":
            return {"status": "done", "actions": actions}
        actions.append(action)
        if detect_loop(actions, repeat):
            return {"status": "loop_detected", "actions": actions}
        if drift_threshold is not None and goal_relatedness(goal, action) < drift_threshold:
            return {"status": "goal_drift", "actions": actions}
    return {"status": "step_limit", "actions": actions}


if __name__ == "__main__":
    # петля: policy всегда возвращает одно и то же
    print(run_guarded(lambda a: "refresh", max_steps=10))
    # нормальная работа: три шага и финал
    seq = ["search", "read", "answer"]
    print(run_guarded(lambda a: seq[len(a)] if len(a) < len(seq) else "DONE"))
    # бесконечная без повторов → упрётся в лимит
    print(run_guarded(lambda a: f"step_{len(a)}", max_steps=5))
