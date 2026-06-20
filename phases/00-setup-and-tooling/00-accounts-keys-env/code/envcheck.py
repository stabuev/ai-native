"""Парсер .env + валидатор ключей окружения — Build It для урока 0.2.

Без внешних зависимостей и без сети. Разбирает файл .env (KEY=VALUE), понимает
комментарии, `export`, кавычки и inline-комментарии; проверяет, что нужные ключи
заданы и не остались плейсхолдерами. Реальный первый запрос к API — в USE IT.
"""
from __future__ import annotations

# Значения, которые выдают незаполненный .env.
PLACEHOLDERS = {"", "your-key-here", "changeme", "xxx", "...", "todo"}

# Грубая проверка формата по префиксу (без сети). Пустой префикс — не проверяем.
KEY_HINTS = {
    "ANTHROPIC_API_KEY": "sk-ant-",
    "OPENAI_API_KEY": "sk-",
    "GOOGLE_API_KEY": "",
}


def _clean_value(val: str) -> str:
    """Снять кавычки и inline-комментарий со значения."""
    val = val.strip()
    if val[:1] in {'"', "'"}:          # значение в кавычках — берём содержимое
        quote = val[0]
        return val[1:].split(quote, 1)[0]
    return val.split(" #", 1)[0].strip()   # без кавычек — режем ` #комментарий`


def parse_env(text: str) -> dict:
    """Текст .env -> dict. Пустые строки и комментарии игнорируются."""
    env = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        env[key.strip()] = _clean_value(val)
    return env


def validate(env: dict, required) -> list[str]:
    """Список проблем по требуемым ключам (пустой список = всё в порядке)."""
    problems = []
    for key in required:
        val = env.get(key)
        if val is None:
            problems.append(f"{key}: отсутствует")
        elif val.lower() in PLACEHOLDERS:
            problems.append(f"{key}: похоже на плейсхолдер")
        else:
            hint = KEY_HINTS.get(key, "")
            if hint and not val.startswith(hint):
                problems.append(f"{key}: не похоже на ключ (ожидался префикс {hint!r})")
    return problems


if __name__ == "__main__":
    sample = """
    # пример .env
    export ANTHROPIC_API_KEY="sk-ant-demo123"   # ключ Anthropic
    OPENAI_API_KEY=your-key-here
    """
    env = parse_env(sample)
    print("Распознано ключей:", list(env))
    problems = validate(env, ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY"])
    print("Проблемы:", problems or "нет")
