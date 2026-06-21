# Урок 6.4 · Тест и подключение

**Фаза 6 — Инструменты и протоколы (MCP)** · **Результат фазы:** Объяснить tool use изнутри и поднять собственный MCP-сервер с контролем доступа.
<!-- **Requires:** Node/npx (MCP Inspector) и клиент (Claude Desktop/Cursor) — только для блока USE IT -->

> **MOTTO.** Сначала прогони сервер инспектором, потом подключай к клиенту — не наоборот.

## PROBLEM

«Подключил сервер к Claude, не работает» — и непонятно, где сломалось: в сервере, транспорте или конфиге. Поэтому сервер сначала **тестируют** изолированно (MCP Inspector), проверяя протокол, и только потом подключают к клиенту. Соберём мини-инспектор, чтобы понять, что именно он проверяет.

## CONCEPT

```
сервер handle(request)
   │ инспектор гоняет протокол:
   ├─ initialize      → есть serverInfo, protocolVersion?
   ├─ tools/list      → список, у инструментов name + inputSchema?
   ├─ неизвестный метод → корректный error -32601?
   └─ tools/call      → result с content?
   ▼
отчёт: конформен / есть проблемы → потом подключение к клиенту
```

## BUILD IT

Мини-инспектор протокола, без зависимостей: [`code/mcp_inspector.py`](../code/mcp_inspector.py).

- `inspect(handle, call=None)` — прогоняет initialize/tools-list/неизвестный метод/(опц.) вызов и собирает отчёт по проверкам;
- `demo_handle` — минимально конформный сервер для демо.

```bash
python code/mcp_inspector.py
pytest code -q
```

Инспектор работает с любым сервером вида `handle(request)->response` (в т.ч. с `MiniMCP` из 6.3). Тест проверяет: конформный сервер проходит, сломанный — нет.

## USE IT

Готовый MCP Inspector и подключение к клиенту:

```bash
npx @modelcontextprotocol/inspector node build/index.js   # UI на localhost:6274
mcp dev server.py                                          # быстрый запуск инспектора (Python SDK)
mcp install server.py                                      # установить сервер в Claude Desktop
```

- **MCP Inspector** — вкладки Tools/Resources/Prompts/Logs; видно реальные запросы/ответы.
- **Claude Desktop / Cursor** — добавить сервер в конфиг; клиент сделает discovery и покажет инструменты.

## SHIP IT

**Артефакт:** Документированный сервер с примерами → [`outputs/mcp-server-guide.md`](../outputs/mcp-server-guide.md)

Гайд: как протестировать сервер инспектором, как подключить к Claude Desktop/Cursor, примеры запросов и типовые ошибки. Дальше: безопасность и доступ (6.5).

## Материалы

- [MCP — Inspector](https://modelcontextprotocol.io/docs/tools/inspector) — визуальный тест-инструмент.
- [modelcontextprotocol/inspector](https://github.com/modelcontextprotocol/inspector) — исходники и CLI-режим.
- [MCP — Build an MCP server](https://modelcontextprotocol.io/docs/develop/build-server) — установка сервера в Claude Desktop.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
