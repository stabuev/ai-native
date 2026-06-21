from data_classifier import detect_pii, classify_sensitivity, redact, can_send


def test_detects_email_and_phone():
    found = {f["type"] for f in detect_pii("пиши на a@b.com или +7 999 123 45 67")}
    assert "email" in found
    assert "phone" in found


def test_detects_secret_and_card():
    assert any(f["type"] == "secret" for f in detect_pii("ключ sk-abcd1234efgh"))
    assert any(f["type"] == "card" for f in detect_pii("карта 4111 1111 1111 1111"))


def test_classify_levels():
    assert classify_sensitivity("ключ sk-abcd1234efgh") == "restricted"
    assert classify_sensitivity("почта a@b.com") == "confidential"
    assert classify_sensitivity("для служебного пользования") == "internal"
    assert classify_sensitivity("обычный текст про погоду") == "public"


def test_redact_masks_pii():
    masked = redact("почта a@b.com")
    assert "a@b.com" not in masked
    assert "[EMAIL]" in masked


def test_can_send_respects_threshold():
    assert can_send("public") is True
    assert can_send("restricted") is False           # порог по умолчанию internal
    assert can_send("confidential", max_allowed="confidential") is True
