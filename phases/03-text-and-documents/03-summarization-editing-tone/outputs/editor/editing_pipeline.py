"""Резюмирование, редактура, тон: текстовый пайплайн — Build It для урока 3.1.

Без зависимостей. Пайплайн «черновик → редактура → тон»: extractive-резюме
(частотная оценка предложений), чистка (filler-слова и пробелы), смена тона
(словарь маркеров). Стадии — детерминированные функции (офлайн); в USE IT
каждую стадию играет модель.
"""
import re
from collections import Counter

_SENT = re.compile(r"[^.!?]+[.!?]?")
FILLER_WORDS = {"очень", "просто", "буквально", "реально", "вообще", "типа"}


def split_sentences(text):
    return [s.strip() for s in _SENT.findall(text) if s.strip()]


def summarize_extractive(text, n=2):
    """Черновик: n самых «важных» предложений по частоте значимых слов."""
    sents = split_sentences(text)
    if len(sents) <= n:
        return " ".join(sents)
    words = re.findall(r"\w+", text.lower())
    freq = Counter(w for w in words if len(w) > 3)

    def score(s):
        return sum(freq[w] for w in re.findall(r"\w+", s.lower()))

    top = sorted(range(len(sents)), key=lambda i: score(sents[i]), reverse=True)[:n]
    return " ".join(sents[i] for i in sorted(top))      # в исходном порядке


def tighten(text):
    """Редактура: убрать слова-филлеры и схлопнуть пробелы."""
    kept = [w for w in text.split() if w.lower().strip(",.!?") not in FILLER_WORDS]
    return re.sub(r"\s+", " ", " ".join(kept)).strip()


TONE = {
    "formal": {"привет": "Здравствуйте", "пока": "До свидания", "спасибо": "Благодарю"},
    "casual": {"здравствуйте": "привет", "благодарю": "спасибо"},
}


def set_tone(text, tone):
    """Тон: заменить маркеры по словарю выбранного тона."""
    for src, dst in TONE.get(tone, {}).items():
        text = re.sub(src, dst, text, flags=re.IGNORECASE)
    return text


def run_pipeline(text, stages):
    """Прогнать текст через список стадий (callable: str -> str)."""
    for fn in stages:
        text = fn(text)
    return text


if __name__ == "__main__":
    doc = ("Кошки любят рыбу. Кошки очень любят свежую рыбу. "
           "Погода сегодня внезапно испортилась.")
    pipeline = [lambda t: summarize_extractive(t, 1), tighten,
                lambda t: set_tone(t, "formal")]
    print("Исходник:", doc)
    print("Итог    :", run_pipeline(doc, pipeline))
