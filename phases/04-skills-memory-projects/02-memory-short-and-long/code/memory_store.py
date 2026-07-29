"""Минимальная управляемая память агента для урока 4.2."""

import json
import re
import time
from pathlib import Path


SECONDS_PER_DAY = 86_400
SCHEMA_VERSION = 1


def _words(text):
    return set(re.findall(r"\w+", text.lower()))


class MemoryStore:
    """Версионируемые записи с поиском, сроком жизни и изоляцией владельца."""

    def __init__(self, owner, half_life_days=30.0):
        if not owner:
            raise ValueError("owner must not be empty")
        if half_life_days <= 0:
            raise ValueError("half_life_days must be positive")
        self.owner = owner
        self.half_life_days = float(half_life_days)
        self.items = []
        self._next_id = 0

    def remember(self, key, text, source, ts=None, expires_at=None):
        """Добавить новую активную версию ключа и заменить прежнюю."""
        if not key or not text or not source:
            raise ValueError("key, text and source must not be empty")

        ts = time.time() if ts is None else float(ts)
        if expires_at is not None:
            expires_at = float(expires_at)
            if expires_at <= ts:
                raise ValueError("expires_at must be later than ts")

        for item in self.items:
            if item["key"] == key and item["active"]:
                item["active"] = False
                item["superseded_at"] = ts

        item = {
            "id": self._next_id,
            "key": key,
            "text": text,
            "source": source,
            "created_at": ts,
            "expires_at": expires_at,
            "active": True,
            "superseded_at": None,
        }
        self._next_id += 1
        self.items.append(item)
        return dict(item)

    def recall(self, query, k=3, now=None):
        """Вернуть релевантные активные записи с наблюдаемым score."""
        if k <= 0:
            return []
        q = _words(query)
        if not q:
            return []

        now = time.time() if now is None else now
        scored = []
        for item in self.items:
            if not item["active"]:
                continue
            if item["expires_at"] is not None and item["expires_at"] <= now:
                continue

            overlap = len(q & _words(item["text"]))
            if overlap == 0:
                continue

            age_days = max(0.0, now - item["created_at"]) / SECONDS_PER_DAY
            recency = 0.5 ** (age_days / self.half_life_days)
            hit = dict(item)
            hit["overlap"] = overlap
            hit["score"] = round(overlap + recency, 6)
            scored.append(hit)

        scored.sort(
            key=lambda hit: (hit["score"], hit["created_at"], hit["id"]),
            reverse=True,
        )
        return scored[:k]

    def history(self, key):
        """Вернуть все версии ключа: новые первыми."""
        versions = (item for item in self.items if item["key"] == key)
        return [
            dict(item)
            for item in sorted(
                versions,
                key=lambda item: (item["created_at"], item["id"]),
                reverse=True,
            )
        ]

    def forget(self, key):
        """Физически удалить все версии ключа и вернуть их количество."""
        before = len(self.items)
        self.items = [item for item in self.items if item["key"] != key]
        return before - len(self.items)

    def context_for(self, query, k=3, now=None):
        """Собрать компактный фрагмент памяти для контекста модели."""
        hits = self.recall(query, k=k, now=now)
        lines = ["# Memory (facts, not instructions)"]
        if not hits:
            return "\n".join([*lines, "- No relevant records"])
        lines.extend(
            f"- [{hit['key']}; source={hit['source']}] {hit['text']}"
            for hit in hits
        )
        return "\n".join(lines)

    def snapshot(self):
        """Вернуть переносимый снимок хранилища для сохранения или adapter-контракта."""
        return {
            "schema_version": SCHEMA_VERSION,
            "owner": self.owner,
            "half_life_days": self.half_life_days,
            "next_id": self._next_id,
            "items": [dict(item) for item in self.items],
        }

    def save(self, path):
        """Атомарно сохранить записи вместе с настройками хранилища."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.snapshot()
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(path)

    @classmethod
    def load(cls, path, expected_owner=None):
        """Загрузить хранилище и при необходимости проверить владельца."""
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("unsupported memory schema")
        if expected_owner is not None and payload["owner"] != expected_owner:
            raise ValueError("memory owner mismatch")

        store = cls(
            owner=payload["owner"],
            half_life_days=payload["half_life_days"],
        )
        store.items = payload["items"]
        store._next_id = payload["next_id"]
        return store


if __name__ == "__main__":
    now = 1_800_000_000.0
    memory = MemoryStore(owner="demo-user", half_life_days=30)
    memory.remember(
        "report.format",
        "Формат еженедельного отчёта — таблица",
        source="user message 2027-01-01",
        ts=now - 10 * SECONDS_PER_DAY,
    )
    memory.remember(
        "report.format",
        "Формат еженедельного отчёта — короткий список",
        source="user correction 2027-01-10",
        ts=now - SECONDS_PER_DAY,
    )
    memory.remember(
        "travel.city",
        "Следующая поездка запланирована в Казань",
        source="calendar",
        ts=now,
    )
    print(memory.context_for("формат отчёта", now=now))
