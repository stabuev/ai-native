from a2a import AgentCard, find_agent, send_task, route_and_run

CARDS = [
    AgentCard("sql-agent", ["sql", "база", "запрос"], lambda t: "SELECT ..."),
    AgentCard("doc-agent", ["документ", "поиск", "rag"], lambda t: "3 документа"),
]


def test_find_agent_matches_by_skill():
    assert find_agent("сделай sql запрос", CARDS).name == "sql-agent"
    assert find_agent("поиск по документам", CARDS).name == "doc-agent"


def test_find_agent_no_match_returns_none():
    assert find_agent("нарисуй картинку", CARDS) is None


def test_send_task_envelope():
    env = send_task("sql запрос", CARDS[0])
    assert env["status"] == "done"
    assert env["agent"] == "sql-agent"
    assert env["result"] == "SELECT ..."


def test_send_task_no_agent():
    env = send_task("задача", None)
    assert env["status"] == "no_agent"
    assert env["result"] is None


def test_route_and_run_end_to_end():
    assert route_and_run("поиск документ", CARDS)["agent"] == "doc-agent"
