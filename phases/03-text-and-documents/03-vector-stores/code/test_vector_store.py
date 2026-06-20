from vector_store import VectorStore, embed, cosine, DIM


def _store():
    s = VectorStore()
    s.add("cats", "кошки любят спать и рыбу")
    s.add("dogs", "собаки любят прогулки и мяч")
    s.add("py", "python язык программирования")
    return s


def test_embed_is_fixed_dim_and_deterministic():
    v1, v2 = embed("кошки и рыба"), embed("кошки и рыба")
    assert len(v1) == DIM
    assert v1 == v2                      # детерминированно (стабильный хеш)


def test_query_returns_nearest():
    hits = _store().query("кошки и рыба", k=1)
    assert hits[0]["id"] == "cats"


def test_topk_limits():
    assert len(_store().query("любят", k=2)) == 2


def test_save_load_roundtrip(tmp_path):
    s = _store()
    path = tmp_path / "store.json"
    s.save(path)
    loaded = VectorStore().load(path)
    assert loaded.query("python", k=1)[0]["id"] == "py"
    assert loaded.items == s.items       # данные сохранились без потерь


def test_cosine_bounds():
    assert cosine(embed("кошки"), embed("кошки")) == 1.0
    assert cosine(embed("кошки"), embed("python")) < 1.0
