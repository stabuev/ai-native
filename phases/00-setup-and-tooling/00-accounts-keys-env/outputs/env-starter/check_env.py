"""check_env.py — самодостаточный валидатор окружения (drop-in, без зависимостей).

Запуск:  python check_env.py [путь_к_.env]   (по умолчанию ./.env)
Код выхода 0 — всё ок, 1 — есть проблемы. Сети не делает.
"""
import sys
from pathlib import Path

PLACEHOLDERS = {"", "your-key-here", "changeme", "xxx", "...", "todo"}
KEY_HINTS = {"ANTHROPIC_API_KEY": "sk-ant-", "OPENAI_API_KEY": "sk-", "GOOGLE_API_KEY": ""}
REQUIRED = list(KEY_HINTS)


def _clean(val):
    val = val.strip()
    if val[:1] in {'"', "'"}:
        return val[1:].split(val[0], 1)[0]
    return val.split(" #", 1)[0].strip()


def parse_env(text):
    env = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        key, _, val = line.partition("=")
        env[key.strip()] = _clean(val)
    return env


def validate(env, required=REQUIRED):
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
                problems.append(f"{key}: ожидался префикс {hint!r}")
    return problems


if __name__ == "__main__":
    path = Path(sys.argv[1] if len(sys.argv) > 1 else ".env")
    if not path.exists():
        print(f"Нет файла {path}. Скопируй .env.example в .env и заполни.")
        sys.exit(1)
    problems = validate(parse_env(path.read_text(encoding="utf-8")))
    if problems:
        print("Проблемы окружения:")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("Окружение в порядке: все ключи заданы.")
