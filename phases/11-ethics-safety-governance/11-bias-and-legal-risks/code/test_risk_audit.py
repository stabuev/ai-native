from risk_audit import audit, severity_counts


def test_flags_bias_term():
    findings = audit("Все женщины хуже водят машину")
    assert any(f["category"] == "bias" for f in findings)


def test_flags_overclaim():
    findings = audit("Я гарантирую стопроцентный результат")
    assert any(f["category"] == "overclaim" for f in findings)


def test_flags_long_quote_as_copyright():
    text = 'Источник: «' + " ".join(["слово"] * 25) + '».'
    findings = audit(text)
    assert any(f["category"] == "copyright" for f in findings)


def test_clean_text_no_findings():
    assert audit("Сегодня солнечно, рекомендуем взять зонт на всякий случай.") == []


def test_severity_counts():
    findings = audit("Все мужчины всегда правы, гарантирую")
    counts = severity_counts(findings)
    assert counts.get("high", 0) >= 1        # bias
    assert counts.get("medium", 0) >= 1      # overclaim
