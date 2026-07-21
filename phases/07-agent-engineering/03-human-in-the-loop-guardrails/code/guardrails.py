"""Human-in-the-loop и guardrails — Build It для урока 7.3.

Без зависимостей. Между решением агента и действием ставим заслон: опасные
действия требуют подтверждения человека, а валидаторы проверяют аргументы до
исполнения. Так автономность не превращается в «удалил прод по галлюцинации».
"""

# Действия с необратимым/значимым эффектом — требуют подтверждения.
DANGEROUS = {"delete", "send_money", "send_email", "deploy", "drop_table"}


class GuardrailError(Exception):
    pass


def requires_confirmation(tool):
    return tool in DANGEROUS


def run_action(action, tools, confirm=None, validators=None):
    """Исполнить action={tool, args} через заслоны.

    validators: список callable(action)->(ok, reason). confirm: callable(action)->bool.
    """
    tool = action["tool"]
    args = action.get("args", {})

    for validate in (validators or []):                 # 1) валидация аргументов
        ok, reason = validate(action)
        if not ok:
            raise GuardrailError(f"валидация не пройдена: {reason}")

    if requires_confirmation(tool):                     # 2) подтверждение человека
        if confirm is None or not confirm(action):
            raise GuardrailError(f"действие '{tool}' не подтверждено")

    if tool not in tools:                               # 3) известный инструмент
        raise GuardrailError(f"неизвестный инструмент: {tool}")
    return tools[tool](**args)


def amount_limit(max_amount):
    """Валидатор: запретить перевод сумм больше лимита."""
    def check(action):
        amount = action.get("args", {}).get("amount", 0)
        if amount > max_amount:
            return False, f"сумма {amount} > лимита {max_amount}"
        return True, "ok"
    return check


if __name__ == "__main__":
    tools = {"read": lambda **k: "данные", "send_money": lambda amount, to: f"перевод {amount}→{to}"}
    print(run_action({"tool": "read", "args": {}}, tools))                      # безопасно
    # опасное действие с подтверждением и лимитом:
    print(run_action({"tool": "send_money", "args": {"amount": 50, "to": "Иван"}},
                     tools, confirm=lambda a: True, validators=[amount_limit(100)]))
    try:
        run_action({"tool": "send_money", "args": {"amount": 500, "to": "X"}},
                   tools, confirm=lambda a: True, validators=[amount_limit(100)])
    except GuardrailError as e:
        print("Заблокировано:", e)
