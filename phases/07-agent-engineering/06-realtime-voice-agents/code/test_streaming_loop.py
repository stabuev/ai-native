from streaming_loop import StreamingAgent, first_token_latency


def test_full_response_when_no_interrupt():
    agent = StreamingAgent()
    said = agent.respond(["a", "b", "c"])
    assert said == ["a", "b", "c"]
    assert agent.state == "idle"


def test_barge_in_interrupts():
    agent = StreamingAgent()
    said = agent.respond(["a", "b", "c", "d"], interrupt_after=2)
    assert said == ["a", "b"]
    assert agent.state == "interrupted"


def test_transcript_records_turns():
    agent = StreamingAgent()
    agent.respond(["a"])
    agent.respond(["x", "y", "z"], interrupt_after=1)
    assert len(agent.transcript) == 2
    assert agent.transcript[0]["interrupted"] is False
    assert agent.transcript[1]["interrupted"] is True


def test_first_token_latency():
    assert first_token_latency([0.18, 0.05]) == 0.18
    assert first_token_latency([]) is None
