from mini_mcp_server import server


def _req(method, rid=1, params=None):
    r = {"jsonrpc": "2.0", "id": rid, "method": method}
    if params is not None:
        r["params"] = params
    return r


def test_initialize_returns_server_info():
    res = server.handle(_req("initialize"))["result"]
    assert res["serverInfo"]["name"] == "demo-server"
    assert "protocolVersion" in res


def test_tools_list_includes_schemas():
    tools = server.handle(_req("tools/list"))["result"]["tools"]
    names = {t["name"] for t in tools}
    assert {"echo", "add"} <= names
    assert all("inputSchema" in t for t in tools)


def test_tools_call_executes():
    res = server.handle(_req("tools/call", params={"name": "add", "arguments": {"a": 2, "b": 3}}))
    assert res["result"]["content"][0]["text"] == "5"


def test_unknown_tool_is_jsonrpc_error():
    res = server.handle(_req("tools/call", params={"name": "nope", "arguments": {}}))
    assert res["error"]["code"] == -32602


def test_unknown_method_is_jsonrpc_error():
    res = server.handle(_req("no/such"))
    assert res["error"]["code"] == -32601
