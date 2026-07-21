from structured_output import extract_json, validate_schema, SCHEMA


def test_extract_json_from_fenced_and_plain():
    fenced = '```json\n{"a": 1}\n```'
    assert extract_json(fenced) == {"a": 1}
    assert extract_json('{"b": 2}') == {"b": 2}


def test_valid_object_passes():
    obj = {"title": "Баг в оплате", "priority": 3, "urgent": False}
    assert validate_schema(obj, SCHEMA) == []


def test_missing_required_field_flagged():
    errors = validate_schema({"priority": 1}, SCHEMA)
    assert any("title" in e and "обязательное" in e for e in errors)


def test_wrong_type_flagged():
    errors = validate_schema({"title": "X", "priority": "high"}, SCHEMA)
    assert any("priority" in e for e in errors)


def test_boolean_is_not_accepted_as_integer():
    errors = validate_schema({"title": "X", "priority": True}, SCHEMA)
    assert any("priority" in e and "boolean" in e for e in errors)


def test_non_dict_root_flagged():
    assert validate_schema([1, 2, 3], SCHEMA) == ["корень: ожидался объект (dict)"]
