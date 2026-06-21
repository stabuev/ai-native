# Артефакт: документированный MCP-сервер с примерами

Как протестировать сервер и подключить к клиенту. Инспектор — [`code/mcp_inspector.py`](../code/mcp_inspector.py); сервер — урок 6.3.

## 1. Тест протокола (свой инспектор)

```python
from mcp_inspector import inspect
from mini_mcp_server import server          # из урока 6.3
report = inspect(server.handle, call=("add", {"a": 2, "b": 3}))
assert report["ok"], report["checks"]
```

## 2. Тест готовым MCP Inspector

```bash
mcp dev server.py                                          # Python SDK: поднимет инспектор
npx @modelcontextprotocol/inspector node build/index.js   # любой сервер; UI на :6274
```

Проверь вкладки: **Tools** (вызови с аргументами), **Resources**, **Prompts**, **Logs** (реальные JSON-RPC сообщения).

## 3. Подключение к клиенту

```bash
mcp install server.py --name my-server -v API_KEY=...      # в Claude Desktop
```

- **Claude Desktop / Claude Code** — сервер появится в списке инструментов после рестарта клиента.
- **Cursor** — добавить сервер в настройки MCP.
- Транспорт: STDIO (локально), Streamable HTTP (удалённо).

## Примеры запросов (JSON-RPC)

```json
{"jsonrpc":"2.0","id":1,"method":"initialize"}
{"jsonrpc":"2.0","id":2,"method":"tools/list"}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"add","arguments":{"a":2,"b":3}}}
```

## Типовые ошибки

| Симптом | Причина | Решение |
|---|---|---|
| `-32601` | метод не реализован | проверь обработку initialize/tools-list/tools-call |
| Сервер не виден в клиенте | неверный конфиг/транспорт | сверь путь и transport; рестарт клиента |
| Таймаут на вызове | долгий tool | увеличь timeout инспектора/клиента |
| Пустой tools/list | инструменты не зарегистрированы | проверь декораторы `@tool` |
