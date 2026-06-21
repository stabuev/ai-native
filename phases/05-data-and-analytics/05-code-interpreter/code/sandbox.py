"""Code Interpreter: упрощённый sandbox-исполнитель — Build It для урока 5.2.

Без зависимостей. Модель пишет код — sandbox его исполняет и возвращает результат
(так работает Code Interpreter / Advanced Data Analysis). Здесь УЧЕБНЫЙ песок:
ограниченные builtins + статическая проверка опасных конструкций.

ВНИМАНИЕ: это не настоящая изоляция, а демонстрация идеи. Для прода нужен реальный
sandbox (контейнер, seccomp, отдельный процесс с лимитами) — см. урок 6.5.
"""

SAFE_BUILTINS = {
    "len": len, "sum": sum, "min": min, "max": max, "sorted": sorted, "range": range,
    "abs": abs, "round": round, "map": map, "filter": filter, "list": list,
    "dict": dict, "set": set, "tuple": tuple, "enumerate": enumerate, "zip": zip,
    "float": float, "int": int, "str": str, "bool": bool,
}

FORBIDDEN = ("import", "__", "open(", "exec(", "eval(", "compile(", "input(",
             "os.", "sys.", "subprocess", "globals(", "locals(", "getattr(")


class SandboxError(Exception):
    pass


def unsafe_tokens(code):
    """Список запрещённых конструкций, найденных в коде (пустой = чисто)."""
    return [t for t in FORBIDDEN if t in code]


def run_code(code, data=None):
    """Исполнить код в ограниченном окружении. Результат — переменная `result`."""
    bad = unsafe_tokens(code)
    if bad:
        raise SandboxError(f"запрещённые конструкции: {bad}")
    env = {"__builtins__": SAFE_BUILTINS}
    local = {"data": data} if data is not None else {}
    exec(code, env, local)            # noqa: S102 — учебный sandbox, см. оговорку выше
    if "result" not in local:
        raise SandboxError("код не присвоил переменную result")
    return local["result"]


if __name__ == "__main__":
    print(run_code("result = sum(data) / len(data)", data=[10, 20, 30]))   # среднее
    try:
        run_code("import os; result = os.listdir('.')")
    except SandboxError as e:
        print("Заблокировано:", e)
