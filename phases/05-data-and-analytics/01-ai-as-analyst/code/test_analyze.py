from analyze import load_csv, aggregate, top_n, CSV_DEMO

ROWS = load_csv(CSV_DEMO)


def test_load_csv_parses_rows():
    assert len(ROWS) == 5
    assert ROWS[0]["region"] == "Москва" and ROWS[0]["amount"] == "100"


def test_aggregate_sum_by_region():
    by_region = aggregate(ROWS, "region", "amount", "sum")
    assert by_region["Москва"] == 150
    assert by_region["Питер"] == 100


def test_aggregate_count_and_mean():
    assert aggregate(ROWS, "region", "amount", "count")["Москва"] == 2
    by_product_mean = aggregate(ROWS, "product", "amount", "mean")
    assert by_product_mean["A"] == (100 + 30 + 20) / 3


def test_top_n_orders_desc():
    by_region = aggregate(ROWS, "region", "amount", "sum")
    top = top_n(by_region, 2)
    assert top[0] == ("Москва", 150)
    assert len(top) == 2
