from memory_store import MemoryStore

NOW = 1000.0


def _store():
    m = MemoryStore(half_life=30.0)
    m.add("пользователь любит кофе без сахара", ts=NOW - 100)
    m.add("пользователь снова заказал кофе латте", ts=NOW - 1)
    m.add("обсуждали отпуск в горах", ts=NOW - 5)
    return m


def test_search_returns_relevant_only():
    hits = _store().search("кофе", now=NOW)
    assert all("кофе" in h["text"] for h in hits)
    assert len(hits) == 2


def test_recency_breaks_ties():
    # обе записи совпадают по слову «кофе», свежая должна быть первой
    top = _store().search("кофе", k=1, now=NOW)[0]
    assert "латте" in top["text"]


def test_recent_returns_newest_first():
    newest = _store().recent(1)[0]            # самый свежий — ts=NOW-1
    assert "латте" in newest["text"]


def test_no_match_returns_empty():
    assert _store().search("квантовая физика", now=NOW) == []


def test_save_load_roundtrip(tmp_path):
    m = _store()
    path = tmp_path / "mem.json"
    m.save(path)
    loaded = MemoryStore().load(path)
    assert loaded.items == m.items
    assert "кофе" in loaded.search("кофе", k=1, now=NOW)[0]["text"]
