import unittest

from nl_to_sql import (
    DEMO_ROWS,
    compile_query,
    reconcile_total,
    run_read_only,
)


class IntentToSqlTests(unittest.TestCase):
    def test_paid_revenue_adds_required_status_filter(self):
        compiled = compile_query(
            {
                "metric": "paid_revenue",
                "dimensions": ["region"],
                "filters": {"quarter": "Q2"},
            }
        )

        self.assertEqual(
            compiled["sql"],
            "SELECT region, SUM(amount) AS paid_revenue FROM sales "
            "WHERE quarter = ? AND status = ? "
            "GROUP BY region ORDER BY region",
        )
        self.assertEqual(compiled["params"], ("Q2", "paid"))
        self.assertEqual(compiled["semantic_version"], "1.0")
        self.assertEqual(
            compiled["filters"],
            {"status": "paid", "quarter": "Q2"},
        )

    def test_execution_matches_the_verified_5_1_and_5_2_result(self):
        compiled = compile_query(
            {
                "metric": "paid_revenue",
                "dimensions": ["region"],
                "filters": {"quarter": "Q2"},
            }
        )
        result = run_read_only(compiled, DEMO_ROWS)

        self.assertEqual(
            result,
            [
                {"region": "Казань", "paid_revenue": 20.0},
                {"region": "Москва", "paid_revenue": 150.0},
                {"region": "Питер", "paid_revenue": 30.0},
            ],
        )
        self.assertEqual(
            reconcile_total(compiled, result, expected_total=200),
            {
                "metric": "paid_revenue",
                "expected_total": 200.0,
                "actual_total": 200.0,
                "matches": True,
            },
        )

    def test_metric_required_filter_cannot_be_overridden(self):
        with self.assertRaisesRegex(ValueError, "требует status='paid'"):
            compile_query(
                {
                    "metric": "paid_revenue",
                    "dimensions": ["region"],
                    "filters": {"quarter": "Q2", "status": "refunded"},
                }
            )

    def test_unknown_metric_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "неизвестная метрика"):
            compile_query(
                {
                    "metric": "revenue",
                    "dimensions": ["region"],
                    "filters": {"quarter": "Q2"},
                }
            )

    def test_unknown_dimension_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "неизвестное измерение"):
            compile_query(
                {
                    "metric": "paid_revenue",
                    "dimensions": ["manager"],
                    "filters": {"quarter": "Q2"},
                }
            )

    def test_dimension_ids_must_be_strings(self):
        with self.assertRaisesRegex(ValueError, "строковым ID"):
            compile_query(
                {
                    "metric": "paid_revenue",
                    "dimensions": [{"column": "region"}],
                    "filters": {"quarter": "Q2"},
                }
            )

    def test_unknown_filter_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "неизвестный фильтр"):
            compile_query(
                {
                    "metric": "paid_revenue",
                    "dimensions": ["region"],
                    "filters": {"year": 2026},
                }
            )

    def test_filter_value_is_a_parameter_not_sql_text(self):
        suspicious_value = "Q2' OR 1=1 --"
        compiled = compile_query(
            {
                "metric": "paid_revenue",
                "dimensions": ["region"],
                "filters": {"quarter": suspicious_value},
            }
        )

        self.assertNotIn(suspicious_value, compiled["sql"])
        self.assertIn(suspicious_value, compiled["params"])
        self.assertEqual(run_read_only(compiled, DEMO_ROWS), [])

    def test_runner_rejects_non_select_statement(self):
        with self.assertRaisesRegex(ValueError, "разрешён только один SELECT"):
            run_read_only(
                {"sql": "UPDATE sales SET amount = 0", "params": ()},
                DEMO_ROWS,
            )

    def test_total_without_dimension_is_still_200(self):
        compiled = compile_query(
            {
                "metric": "paid_revenue",
                "dimensions": [],
                "filters": {"quarter": "Q2"},
            }
        )

        self.assertEqual(
            run_read_only(compiled, DEMO_ROWS),
            [{"paid_revenue": 200.0}],
        )


if __name__ == "__main__":
    unittest.main()
