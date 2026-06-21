import pytest
from mcp_security import Principal, is_safe_path, check_access, guarded_call

READER = Principal("reader", allowed_tools={"read_file"}, can_write=False)
EDITOR = Principal("editor", allowed_tools={"read_file", "write_file"}, can_write=True)


def test_allowed_read_passes():
    ok, _ = check_access(READER, "read_file", {"path": "reports/q2.csv"})
    assert ok


def test_disallowed_tool_denied():
    ok, reason = check_access(READER, "write_file", {"path": "x"})
    assert not ok and "не разрешён" in reason


def test_write_denied_without_write_right():
    p = Principal("p", allowed_tools={"write_file"}, can_write=False)
    ok, reason = check_access(p, "write_file", {"path": "x"})
    assert not ok and "запис" in reason


def test_path_traversal_blocked():
    assert is_safe_path("reports/q2.csv") is True
    assert is_safe_path("../etc/passwd") is False
    assert is_safe_path("/etc/passwd") is False
    ok, reason = check_access(EDITOR, "read_file", {"path": "../../secret"})
    assert not ok and "traversal" in reason


def test_guarded_call_audits_and_blocks():
    audit = []
    assert guarded_call(READER, "read_file", lambda path: f"read {path}",
                        {"path": "a.txt"}, audit) == "read a.txt"
    with pytest.raises(PermissionError):
        guarded_call(READER, "write_file", lambda **k: None, {"path": "a.txt"}, audit)
    assert len(audit) == 2 and audit[-1]["allowed"] is False
