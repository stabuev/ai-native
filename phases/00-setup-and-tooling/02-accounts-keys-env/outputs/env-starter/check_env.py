"""Локально проверить, что настроен API-ключ хотя бы одного провайдера.

Скрипт не использует сторонние библиотеки, не обращается к сети и не печатает
значения ключей. Успешная проверка подтверждает только наличие и грубый формат,
но не действительность ключа или доступ к конкретной модели.
"""

from __future__ import annotations

import sys
from pathlib import Path


PLACEHOLDERS = {"your-key-here", "changeme", "xxx", "...", "todo"}
PROVIDERS = {
    "ANTHROPIC_API_KEY": ("Anthropic", "sk-ant-"),
    "OPENAI_API_KEY": ("OpenAI", "sk-"),
    "GEMINI_API_KEY": ("Google Gemini", ""),
}


def _clean(value: str) -> str:
    """Убрать внешние кавычки и комментарий после значения."""
    value = value.strip()
    if value[:1] in {'"', "'"}:
        quote = value[0]
        return value[1:].split(quote, 1)[0]
    return value.split(" #", 1)[0].strip()


def parse_env(text: str) -> dict[str, str]:
    """Прочитать простые строки KEY=VALUE из текста .env."""
    env: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        key, _, value = line.partition("=")
        env[key.strip()] = _clean(value)
    return env


def validate(env: dict[str, str]) -> tuple[list[str], list[str]]:
    """Вернуть найденные проблемы и названия настроенных провайдеров."""
    problems: list[str] = []
    configured: list[str] = []

    for key, (provider, prefix) in PROVIDERS.items():
        value = env.get(key, "").strip()
        if not value:
            continue
        if value.lower() in PLACEHOLDERS:
            problems.append(f"{key}: осталось учебное значение вместо ключа")
            continue
        if prefix and not value.startswith(prefix):
            problems.append(f"{key}: значение не похоже на ключ {provider}")
            continue
        configured.append(provider)

    if not configured and not problems:
        problems.append("не настроен ни один поддерживаемый API-ключ")

    return problems, configured


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) > 1:
        print("Использование: python check_env.py [путь_к_.env]")
        return 2

    path = Path(args[0] if args else ".env")
    if not path.is_file():
        print(f"Нет файла {path}. Скопируй .env.example в .env.")
        return 1

    problems, configured = validate(parse_env(path.read_text(encoding="utf-8")))
    if problems:
        print("Проблемы окружения:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print("Локальная проверка пройдена. Настроено:", ", ".join(configured))
    print("Важно: действительность ключа и доступ к модели проверяет только API-запрос.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
