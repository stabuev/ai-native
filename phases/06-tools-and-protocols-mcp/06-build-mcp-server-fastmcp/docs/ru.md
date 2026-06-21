# Урок 6.3 · Свой MCP-сервер на FastMCP

**Фаза 6 — Инструменты и протоколы (MCP)** · **Результат фазы:** Объяснить tool use изнутри и поднять собственный MCP-сервер с контролем доступа.
<!-- **Requires:** пакет `mcp` (FastMCP) — только для блока USE IT -->

> **MOTTO.** MCP-сервер — это обработчик JSON-RPC: `initialize`, `tools/list`, `tools/call`.

## PROBLEM

Чтобы понять, что делает FastMCP «по волшебству» за пару декораторов, надо увидеть протокол под капотом. MCP — это JSON-RPC 2.0: клиент шлёт `initialize`, `tools/list`, `tools/call`, сервер отвечает `result`/`error`. Соберём минимальный сервер сами, потом запустим то же на FastMCP.

## CONCEPT

```
client → {"jsonrpc":"2.0","id":1,"method":"initialize"}        → result: serverInfo, capabilities
client → {"method":"tools/list"}                                → result: [{name, inputSchema}]
client → {"method":"tools/call","params":{name, arguments}}     → result: {content:[...]}  | error
```

Коды ошибок JSON-RPC: `-32601` метод не найден, `-32602` неверные параметры, `-32603` внутренняя ошибка. Транспорт — STDIO (локально) или Streamable HTTP (удалённо).

## BUILD IT

Мини MCP-сервер на JSON-RPC, без зависимостей: [`code/mini_mcp_server.py`](../code/mini_mcp_server.py).

- `MiniMCP` + декоратор `@server.tool(name, description, input_schema)`;
- `handle(request)` — обрабатывает `initialize` / `tools/list` / `tools/call`, отдаёт корректный JSON-RPC.

```bash
python code/mini_mcp_server.py
pytest code -q
```

Это «FastMCP вручную»: видно, какие сообщения он формирует. Теперь то же — через настоящий SDK.

## USE IT

То же на **FastMCP** (официальный SDK `mcp`), транспорты STDIO и Streamable HTTP:

```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("Demo")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Сложить два числа"""
    return a + b

if __name__ == "__main__":
    mcp.run(transport="streamable-http")   # или STDIO по умолчанию
```

FastMCP сам строит схемы из type hints и docstring и обрабатывает JSON-RPC — но это ровно то, что мы написали руками.

## SHIP IT

**Артефакт:** Рабочий MCP-сервер → [`outputs/mini_mcp_server.py`](../outputs/mini_mcp_server.py)

Минимальный сервер (echo + add) с корректным JSON-RPC — основа, к которой добавим тесты/подключение (6.4) и контроль доступа (6.5).

## Материалы

- [MCP — Build an MCP server](https://modelcontextprotocol.io/docs/develop/build-server) — пошаговый гайд.
- [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) — официальный SDK с FastMCP.
- [FastMCP](https://gofastmcp.com) — расширенный фреймворк поверх SDK.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
