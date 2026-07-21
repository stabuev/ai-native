"""Тест и подключение MCP: мини-инспектор — Build It для урока 6.4.

Без зависимостей. Инспектор гоняет MCP-сервер по протоколу (initialize →
tools/list → tools/call) и проверяет, что ответы валидны — как делает MCP
Inspector перед подключением сервера к Claude Desktop / Cursor. Работает с любым
сервером вида `handle(request) -> response` (JSON-RPC 2.0).
"""


def _req(method, rid=1, params=None):
    r = {"jsonrpc": "2.0", "id": rid, "method": method}
    if params is not None:
        r["params"] = params
    return r


def inspect(handle, call=None):
    """Проверить соответствие протоколу. call=(name, args) — опц. проверка вызова.

    Возвращает {checks: [(имя, ok)], ok: bool}.
    """
    checks = []

    init = handle(_req("initialize")).get("result", {})
    checks.append(("initialize → result", bool(init)))
    checks.append(("есть serverInfo", "serverInfo" in init))
    checks.append(("есть protocolVersion", "protocolVersion" in init))

    tools = handle(_req("tools/list")).get("result", {}).get("tools")
    checks.append(("tools/list → список", isinstance(tools, list)))
    checks.append(("у инструментов есть name + inputSchema",
                   bool(tools) and all("name" in t and "inputSchema" in t for t in tools)))

    unknown = handle(_req("no/such/method"))
    checks.append(("неизвестный метод → error -32601",
                   unknown.get("error", {}).get("code") == -32601))

    if call:
        name, args = call
        res = handle(_req("tools/call", params={"name": name, "arguments": args}))
        checks.append((f"tools/call {name} → content",
                       "content" in res.get("result", {})))

    return {"checks": checks, "ok": all(ok for _, ok in checks)}


# --- демо-сервер (минимально конформный) ---
def demo_handle(request):
    rid, method = request.get("id"), request.get("method")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2024-11-05", "serverInfo": {"name": "demo", "version": "0.1"}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": [
            {"name": "ping", "inputSchema": {"type": "object", "properties": {}}}]}}
    if method == "tools/call":
        return {"jsonrpc": "2.0", "id": rid,
                "result": {"content": [{"type": "text", "text": "pong"}]}}
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "not found"}}


if __name__ == "__main__":
    report = inspect(demo_handle, call=("ping", {}))
    for name, ok in report["checks"]:
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")
    print("Итог:", "сервер конформен" if report["ok"] else "есть проблемы")
