import pytest
from mcp_architecture import MCPServer, MCPClient


def _server():
    srv = MCPServer("demo")
    srv.add_tool("sum", lambda a, b: a + b, "сложить")
    srv.add_resource("doc://policy", "Возврат в течение 14 дней.")
    srv.add_prompt("greet", "Привет, {name}!")
    return srv


def test_discovery_lists_all_primitives():
    disc = MCPClient(_server()).discover()
    assert disc["tools"][0]["name"] == "sum"
    assert "doc://policy" in disc["resources"]
    assert "greet" in disc["prompts"]


def test_call_tool_executes():
    assert MCPClient(_server()).call("sum", a=2, b=3) == 5


def test_read_resource_and_prompt():
    srv = _server()
    assert "14 дней" in srv.read_resource("doc://policy")
    assert srv.get_prompt("greet", name="Иван") == "Привет, Иван!"


def test_unknown_primitives_raise():
    srv = _server()
    with pytest.raises(KeyError):
        srv.call_tool("nope")
    with pytest.raises(KeyError):
        srv.read_resource("doc://missing")
