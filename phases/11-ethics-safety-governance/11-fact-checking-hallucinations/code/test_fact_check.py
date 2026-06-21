from fact_check import extract_claims, verify_claim, fact_check

SOURCES = [
    "Возврат товара возможен в течение 14 дней с момента покупки.",
    "Гарантия на электронику составляет 12 месяцев.",
]


def test_extract_claims_splits_sentences():
    claims = extract_claims("Первое утверждение. Второе утверждение!")
    assert len(claims) == 2


def test_grounded_claim_supported():
    assert verify_claim("Возврат возможен в течение 14 дней", SOURCES) == "supported"


def test_ungrounded_claim_unsupported():
    assert verify_claim("Гарантия длится 100 лет на всё", SOURCES) == "unsupported"


def test_fact_check_report():
    report = fact_check("Возврат возможен в течение 14 дней. Доставка на Марс бесплатна.", SOURCES)
    statuses = {r["claim"]: r["status"] for r in report}
    assert any(s == "supported" for s in statuses.values())
    assert any(s == "unsupported" for s in statuses.values())
