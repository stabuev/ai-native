"""Skills и SKILL.md: парсер + матчер — Build It для урока 4.1.

Без зависимостей. Скилл — это папка с SKILL.md (frontmatter `name`/`description`
+ инструкция). Здесь парсим frontmatter без PyYAML, валидируем обязательные поля
и выбираем подходящий скилл под запрос по триггерам. Так работает progressive
disclosure: агент грузит инструкцию только релевантного скилла.
"""
import re


def parse_skill(text):
    """SKILL.md -> {name, description, body}. Frontmatter между `---` ... `---`."""
    m = re.match(r"\s*---\s*\n(.*?)\n---\s*\n?(.*)", text, re.DOTALL)
    if not m:
        return {"name": None, "description": None, "body": text.strip()}
    front, body = m.group(1), m.group(2)
    meta = {}
    for line in front.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip().strip('"').strip("'")
    return {"name": meta.get("name"), "description": meta.get("description"),
            "body": body.strip()}


def validate_skill(parsed):
    """Список проблем по обязательным полям skill (пустой = ок)."""
    problems = []
    if not parsed.get("name"):
        problems.append("нет поля name во frontmatter")
    desc = parsed.get("description")
    if not desc:
        problems.append("нет поля description во frontmatter")
    elif len(desc) < 20:
        problems.append("description слишком короткий — добавь триггеры")
    return problems


def _words(text):
    return set(re.findall(r"\w+", (text or "").lower()))


def match_skill(query, skills):
    """Выбрать скилл с наибольшим пересечением слов запроса и description.

    skills: list[parsed]. Возвращает лучший parsed или None (нет совпадений).
    """
    q = _words(query)
    best, best_score = None, 0
    for s in skills:
        score = len(q & _words(s.get("description")))
        if score > best_score:
            best, best_score = s, score
    return best


if __name__ == "__main__":
    sample = (
        "---\n"
        "name: editor\n"
        "description: Редактирует текст: сокращает, чистит, меняет тон письма\n"
        "---\n"
        "# editor\nИнструкция по редактуре...\n"
    )
    parsed = parse_skill(sample)
    print("Распознано:", parsed["name"], "|", parsed["description"][:30])
    print("Проблемы:", validate_skill(parsed) or "нет")
    skills = [parsed, {"name": "calc", "description": "Считает арифметику и числа"}]
    hit = match_skill("отредактируй текст", skills)        # 'текст' есть в описании editor
    print("Под запрос 'отредактируй текст' →", hit["name"] if hit else "нет совпадений")
