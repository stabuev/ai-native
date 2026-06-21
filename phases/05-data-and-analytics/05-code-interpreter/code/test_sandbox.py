import pytest
from sandbox import run_code, unsafe_tokens, SandboxError


def test_runs_allowed_code():
    assert run_code("result = sum(data)", data=[1, 2, 3]) == 6
    assert run_code("result = max(data) - min(data)", data=[5, 1, 9]) == 8


def test_blocks_import():
    with pytest.raises(SandboxError):
        run_code("import os\nresult = 1")


def test_blocks_dunder_and_open():
    assert unsafe_tokens("__import__('os')")
    with pytest.raises(SandboxError):
        run_code("result = open('/etc/passwd').read()")


def test_requires_result_variable():
    with pytest.raises(SandboxError):
        run_code("x = 5")        # result не задан


def test_clean_code_has_no_unsafe_tokens():
    assert unsafe_tokens("result = sorted(data)") == []
