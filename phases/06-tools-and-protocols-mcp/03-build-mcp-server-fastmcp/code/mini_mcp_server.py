"""Свой MCP-сервер: мини JSON-RPC реализация — Build It для урока 6.3.

Без зависимостей. MCP поверх JSON-RPC 2.0: клиент шлёт запросы `initialize`,
`tools/list`, `tools/call`, сервер отвечает result/error. Здесь собран минимальный
сервер, чтобы понять протокол. В USE IT то же делает FastMCP (mcp SDK) поверх
транспортов STDIO / Streamable HTTP — но формат сообщений тот же.
"""
from dataclasses import dataclass
from typing import Callable

PROTOCOL_VERSION = "2024-11-05"


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict
    fn: Callable


class MiniMCP:
    def __init__(self, name, version="0.1.0"):
        self.name = name
        self.version = version
        self.tools = {}

    def tool(self, name, description, input_schema):
        """Декоратор регистрации инструмента."""
        def wrap(fn):
            self.tools[name] = Tool(name, description, input_schema, fn)
            return fn
        return wrap

    def _ok(self, rid, result):
        return {"jsonrpc": "2.0", "id": rid, "result": result}

    def _err(self, rid, code, message):
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}

    def handle(self, request):
        """Обработать один JSON-RPC запрос -> ответ (dict)."""
        rid = request.get("id")
        method = request.get("method")
        if method == "initialize":
            return self._ok(rid, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": self.name, "version": self.version},
            })
        if method == "tools/list":
            return self._ok(rid, {"tools": [
                {"name": t.name, "description": t.description, "inputSchema": t.input_schema}
                for t in self.tools.values()]})
        if method == "tools/call":
            params = request.get("params", {})
            name = params.get("name")
            if name not in self.tools:
                return self._err(rid, -32602, f"unknown tool: {name}")
            try:
                result = self.tools[name].fn(**params.get("arguments", {}))
            except Exception as e:                       # noqa: BLE001 — вернуть как JSON-RPC error
                return self._err(rid, -32603, f"tool error: {e}")
            return self._ok(rid, {"content": [{"type": "text", "text": str(result)}]})
        return self._err(rid, -32601, f"method not found: {method}")


# --- демо-сервер ---
server = MiniMCP("demo-server")


@server.tool("echo", "вернуть переданный текст",
             {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]})
def echo(text):
    return text


@server.tool("add", "сложить a и b",
             {"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
              "required": ["a", "b"]})
def add(a, b):
    return a + b


if __name__ == "__main__":
    print(server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"}))
    print(server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))
    print(server.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                         "params": {"name": "add", "arguments": {"a": 2, "b": 3}}}))
