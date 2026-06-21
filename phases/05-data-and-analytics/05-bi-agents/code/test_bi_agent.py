from bi_agent import investigate, DEMO


def test_plan_has_three_steps():
    steps = investigate(DEMO, "region", "amount")
    assert [s["step"] for s in steps] == ["overview", "breakdown", "top_segment"]


def test_overview_total_is_sum():
    steps = investigate(DEMO, "region", "amount")
    assert steps[0]["total"] == 270


def test_breakdown_aggregates_by_dimension():
    steps = investigate(DEMO, "region", "amount")
    assert steps[1]["values"]["Москва"] == 150


def test_top_segment_and_share():
    top = investigate(DEMO, "region", "amount")[2]
    assert top["segment"] == "Москва"
    assert top["value"] == 150
    assert top["share"] == round(150 / 270, 3)
