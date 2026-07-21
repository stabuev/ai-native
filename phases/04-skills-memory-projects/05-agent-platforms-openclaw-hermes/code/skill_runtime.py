"""Агентные платформы: загрузка скилла в локальный рантайм — Build It 4.5.

Без зависимостей. Платформы вроде OpenClaw/Hermes — это локальный рантайм, который
грузит скиллы (SKILL.md), роутит входящее сообщение в подходящий скилл, исполняет
его и держит память между сообщениями. Здесь собираем уменьшенную версию такого
рантайма. В USE IT — настоящая платформа со скиллами + память + мульти-модель + MCP.
"""
import re


def parse_skill(text):
    """SKILL.md -> {name, description, body} (frontmatter без PyYAML, как в 4.1)."""
    m = re.match(r"\s*---\s*\n(.*?)\n---\s*\n?(.*)", text, re.DOTALL)
    meta, body = {}, text.strip()
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip().strip('"').strip("'")
        body = m.group(2).strip()
    return {"name": meta.get("name"), "description": meta.get("description") or "", "body": body}


def _w(text):
    return set(re.findall(r"\w+", (text or "").lower()))


class Runtime:
    """Локальный агент-рантайм: грузит скиллы, роутит сообщение, держит память."""

    def __init__(self):
        self.skills = {}
        self.handlers = {}
        self.memory = []

    def load(self, skill_text, handler=None):
        s = parse_skill(skill_text)
        self.skills[s["name"]] = s
        if handler:
            self.handlers[s["name"]] = handler
        return s["name"]

    def route(self, message):
        """Выбрать скилл по пересечению слов сообщения и description (как в 4.1)."""
        q = _w(message)
        best, best_score = None, 0
        for name, s in self.skills.items():
            score = len(q & _w(s["description"]))
            if score > best_score:
                best, best_score = name, score
        return best

    def handle(self, message):
        """Обработать сообщение: роут → исполнение → запись в память."""
        self.memory.append(message)
        name = self.route(message)
        if name is None:
            return {"skill": None, "result": "нет подходящего скилла"}
        handler = self.handlers.get(name)
        return {"skill": name, "result": handler(message) if handler else f"[{name}] выполнено"}


EDITOR_SKILL = "---\nname: editor\ndescription: редактирует и сокращает текст письма\n---\n# editor\n"
CALC_SKILL = "---\nname: calc\ndescription: считает арифметику числа и проценты\n---\n# calc\n"

if __name__ == "__main__":
    rt = Runtime()
    rt.load(EDITOR_SKILL, handler=lambda m: "сокращено")
    rt.load(CALC_SKILL, handler=lambda m: "42")
    print(rt.handle("отредактируй текст письма"))
    print(rt.handle("посчитай проценты"))
    print(rt.handle("погода завтра"))
    print("в памяти сообщений:", len(rt.memory))
