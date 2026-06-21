from complexity_router import classify, route


def test_easy_request_is_low():
    assert classify("Переведи фразу на английский") == "low"
    assert route("Переведи фразу на английский") == "gemini-flash"


def test_hard_request_is_high():
    assert classify("Проанализируй архитектуру и оптимизируй код") == "high"
    assert route("Докажи теорему и приведи рассуждение") == "opus-4.8"


def test_medium_default():
    assert classify("Сделай саммари встречи в пять пунктов") == "medium"
    assert route("Сделай саммари встречи в пять пунктов") == "sonnet-4.6"


def test_long_request_escalates_to_high():
    assert classify("a" * 700) == "high"
