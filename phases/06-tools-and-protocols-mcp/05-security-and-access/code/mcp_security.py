"""Безопасность и доступ MCP — Build It для урока 6.5.

Без зависимостей. Слой контроля доступа перед вызовом инструмента: principal с
разрешёнными инструментами и правом записи, проверка прав и аргументов, защита от
обхода путей (path traversal). Идея: MCP-сервер не должен слепо исполнять всё,
что просит модель — между моделью и действием стоит авторизация.
"""
import posixpath
from dataclasses import dataclass, field

# Инструменты, меняющие состояние (требуют отдельного права на запись).
WRITE_TOOLS = {"write_file", "delete_file", "run_sql_write", "send_email"}


@dataclass
class Principal:
    name: str
    allowed_tools: set = field(default_factory=set)
    can_write: bool = False


def is_safe_path(path, allowed_root="/data"):
    """Запретить выход за allowed_root (path traversal, абсолютные пути наружу)."""
    if ".." in path.split("/"):
        return False
    base = path if path.startswith("/") else posixpath.join(allowed_root, path)
    norm = posixpath.normpath(base)
    return norm == allowed_root or norm.startswith(allowed_root + "/")


def check_access(principal, tool, args=None):
    """Разрешён ли вызов tool для principal. Возвращает (allowed, reason)."""
    args = args or {}
    if tool not in principal.allowed_tools:
        return False, f"инструмент '{tool}' не разрешён для {principal.name}"
    if tool in WRITE_TOOLS and not principal.can_write:
        return False, "нет прав на запись"
    if "path" in args and not is_safe_path(args["path"]):
        return False, "недопустимый путь (path traversal)"
    return True, "ok"


def guarded_call(principal, tool, fn, args=None, audit=None):
    """Проверить доступ и (если разрешено) вызвать fn. Пишет в audit-лог."""
    args = args or {}
    allowed, reason = check_access(principal, tool, args)
    if audit is not None:
        audit.append({"principal": principal.name, "tool": tool,
                      "allowed": allowed, "reason": reason})
    if not allowed:
        raise PermissionError(reason)
    return fn(**args)


if __name__ == "__main__":
    reader = Principal("reader", allowed_tools={"read_file"}, can_write=False)
    editor = Principal("editor", allowed_tools={"read_file", "write_file"}, can_write=True)
    print(check_access(reader, "read_file", {"path": "reports/q2.csv"}))   # ok
    print(check_access(reader, "write_file", {"path": "x"}))               # нет инструмента
    print(check_access(editor, "read_file", {"path": "../../etc/passwd"}))  # traversal
