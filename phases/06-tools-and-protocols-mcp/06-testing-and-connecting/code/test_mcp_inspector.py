from mcp_inspector import inspect, demo_handle


def test_conformant_server_passes():
    report = inspect(demo_handle, call=("ping", {}))
    assert report["ok"] is True


def test_broken_server_fails():
    # сервер без serverInfo и без обработки неизвестного метода
    def broken(request):
        return {"jsonrpc": "2.0", "id": request.get("id"), "result": {}}
    report = inspect(broken)
    assert report["ok"] is False
    names = dict(report["checks"])
    assert names["есть serverInfo"] is False


def test_checks_cover_protocol_basics():
    labels = [name for name, _ in inspect(demo_handle)["checks"]]
    assert any("initialize" in s for s in labels)
    assert any("tools/list" in s for s in labels)
    assert any("-32601" in s for s in labels)
