# Урок 6.2 · Архитектура MCP

**Фаза 6 — Инструменты и протоколы (MCP)** · **Результат фазы:** Объяснить tool use изнутри и поднять собственный MCP-сервер с контролем доступа.
<!-- **Requires:** платный API-ключ / клиент с MCP — только для блока USE IT -->

> **MOTTO.** MCP — это USB-C между ИИ и миром: один протокол, три примитива (tools/resources/prompts).

## PROBLEM

В уроке 6.1 инструменты были «вшиты» в приложение. Но у каждого приложения свои инструменты, и переиспользовать их между Claude/Cursor/агентами нельзя. **MCP** стандартизует подключение: один протокол, через который любой клиент находит и зовёт инструменты любого сервера — как USB для периферии.

## CONCEPT

```
   Host (приложение с LLM)
     └─ Client ⇄ Server     (1 client ↔ 1 server, JSON-RPC 2.0)
                   ├─ tools      действия (как POST)
                   ├─ resources  данные (как GET)
                   └─ prompts    заготовки-шаблоны
        discovery (list) → invoke (call)
```

- **Host** — приложение (Claude Desktop, IDE, агент). **Client** — коннектор внутри host (1:1 к серверу). **Server** — отдаёт три примитива.
- Поток: клиент **перечисляет** возможности (discovery), затем **вызывает** (invoke).

## BUILD IT

In-process модель host↔client↔server с тремя примитивами: [`code/mcp_architecture.py`](../code/mcp_architecture.py).

- `MCPServer` — `add_tool/add_resource/add_prompt`, `list_*` (discovery), `call_tool/read_resource/get_prompt` (invoke);
- `MCPClient` — `discover()` и `call()`.

```bash
python code/mcp_architecture.py
pytest code -q
```

Это «MCP без транспорта»: видно роли и три примитива. Транспорт (JSON-RPC) добавим в 6.3.

## USE IT

Подключение готовых MCP-коннекторов (мульти-платформа): десятки серверов уже есть (файлы, БД, GitHub, поиск).

- **Claude Desktop / Claude Code** — добавить сервер в конфиг MCP; клиент сам сделает discovery.
- **Cursor / другие host'ы** — тот же протокол, свои настройки.
- Реестр примеров — `modelcontextprotocol/servers` (референс-реализации).

Один сервер работает в любом MCP-совместимом host — в этом и смысл стандарта.

## SHIP IT

**Артефакт:** Карта MCP под свой стек → [`outputs/mcp-map.md`](../outputs/mcp-map.md)

Карта: какие данные/инструменты вынести в свои MCP-серверы, какие готовые коннекторы подключить, что к какому host'у. Дальше: поднимаем свой сервер (6.3).

## Материалы

- [MCP — Specification](https://modelcontextprotocol.io/specification/2025-11-25) — протокол, примитивы, capability negotiation.
- [Anthropic — Introducing MCP](https://www.anthropic.com/news/model-context-protocol) — зачем нужен стандарт.
- [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) — готовые серверы-примеры.

---
**Часы:** ~4 · **DoD:** `pytest code -q` зелёный, демо запускается, ru.md заполнен. ✅ **Урок готов**
