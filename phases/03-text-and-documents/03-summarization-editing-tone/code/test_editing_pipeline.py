from editing_pipeline import (split_sentences, summarize_extractive, tighten,
                              set_tone, run_pipeline)

DOC = ("Кошки любят рыбу. Кошки очень любят свежую рыбу. "
       "Погода сегодня внезапно испортилась.")


def test_summary_is_shorter_and_keeps_topic():
    s = summarize_extractive(DOC, n=1)
    assert len(split_sentences(s)) == 1
    assert "рыбу" in s.lower()           # частая тема осталась
    assert "погода" not in s.lower()     # редкое предложение отброшено
    assert len(s) < len(DOC)


def test_summary_returns_all_if_few_sentences():
    short = "Одно предложение."
    assert summarize_extractive(short, n=3) == "Одно предложение."


def test_tighten_removes_filler_and_spaces():
    assert tighten("это  очень   просто хороший текст") == "это хороший текст"


def test_set_tone_swaps_markers():
    assert "Здравствуйте" in set_tone("привет, как дела", "formal")


def test_pipeline_composes_stages():
    out = run_pipeline("привет очень всем", [tighten, lambda t: set_tone(t, "formal")])
    assert out == "Здравствуйте всем"
