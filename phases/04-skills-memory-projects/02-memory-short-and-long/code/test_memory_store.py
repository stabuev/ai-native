import pytest

from memory_store import MemoryStore, SECONDS_PER_DAY


NOW = 1_800_000_000.0


def _store():
    memory = MemoryStore(owner="student-42", half_life_days=30)
    memory.remember(
        "report.format",
        "Формат еженедельного отчёта — таблица",
        source="user message",
        ts=NOW - 10 * SECONDS_PER_DAY,
    )
    memory.remember(
        "travel.city",
        "Следующая поездка запланирована в Казань",
        source="calendar",
        ts=NOW,
    )
    return memory


def test_recall_returns_only_relevant_active_records():
    hits = _store().recall("формат отчёта", now=NOW)

    assert [hit["key"] for hit in hits] == ["report.format"]
    assert hits[0]["overlap"] == 2
    assert hits[0]["score"] > 2


def test_new_value_supersedes_old_value_explicitly():
    memory = _store()
    memory.remember(
        "report.format",
        "Формат еженедельного отчёта — короткий список",
        source="user correction",
        ts=NOW - SECONDS_PER_DAY,
    )

    hits = memory.recall("формат отчёта", now=NOW)
    versions = memory.history("report.format")

    assert len(hits) == 1
    assert "короткий список" in hits[0]["text"]
    assert [version["active"] for version in versions] == [True, False]


def test_expired_record_is_not_recalled():
    memory = _store()
    memory.remember(
        "report.deadline",
        "Срок отправки отчёта — пятница",
        source="project chat",
        ts=NOW - 2 * SECONDS_PER_DAY,
        expires_at=NOW - SECONDS_PER_DAY,
    )

    assert memory.recall("срок пятница", now=NOW) == []


def test_fresh_but_irrelevant_record_does_not_enter_context():
    context = _store().context_for("формат отчёта", now=NOW)

    assert "таблица" in context
    assert "Казань" not in context
    assert "source=user message" in context


def test_forget_removes_every_version_of_key_after_save(tmp_path):
    memory = _store()
    memory.remember(
        "report.format",
        "Формат еженедельного отчёта — короткий список",
        source="user correction",
        ts=NOW,
    )

    assert memory.forget("report.format") == 2
    assert memory.history("report.format") == []
    assert memory.recall("формат отчёта", now=NOW) == []

    path = tmp_path / "memory.json"
    memory.save(path)
    loaded = MemoryStore.load(path, expected_owner="student-42")
    assert loaded.history("report.format") == []


def test_save_load_preserves_records_configuration_and_next_id(tmp_path):
    memory = _store()
    path = tmp_path / "memory.json"
    memory.save(path)

    loaded = MemoryStore.load(path, expected_owner="student-42")
    new_item = loaded.remember(
        "report.language",
        "Язык еженедельного отчёта — русский",
        source="user message",
        ts=NOW,
    )

    assert loaded.owner == "student-42"
    assert loaded.half_life_days == 30
    assert loaded.items[:2] == memory.items
    assert new_item["id"] == 2


def test_load_rejects_another_owner_memory(tmp_path):
    path = tmp_path / "memory.json"
    _store().save(path)

    with pytest.raises(ValueError, match="owner mismatch"):
        MemoryStore.load(path, expected_owner="another-user")
