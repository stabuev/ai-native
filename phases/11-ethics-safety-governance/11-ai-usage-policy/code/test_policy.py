from policy import validate_policy, check_usecase, REQUIRED_SECTIONS


def test_full_policy_passes():
    text = "\n".join(REQUIRED_SECTIONS)
    assert validate_policy(text) == []


def test_missing_sections_flagged():
    text = "Допустимые данные\nОтветственность"
    missing = validate_policy(text)
    assert "Запрещённые данные" in missing
    assert "Проверка человеком" in missing


def test_pii_to_external_blocked():
    res = check_usecase(sends_pii=True, external=True)
    assert res["allowed"] is False
    assert "PII" in res["reason"]


def test_automated_decision_blocked():
    assert check_usecase(automated_decision=True)["allowed"] is False


def test_safe_usecase_allowed():
    assert check_usecase(sends_pii=False, external=True)["allowed"] is True
    assert check_usecase(sends_pii=True, external=False)["allowed"] is True
