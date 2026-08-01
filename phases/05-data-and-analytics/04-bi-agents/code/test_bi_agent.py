import unittest

from bi_agent import (
    SEMANTIC,
    choose_next_action,
    execute_intent,
    investigate,
)


QUESTION = "Почему paid_revenue снизилась в Q2 относительно Q1?"


class BiAgentTest(unittest.TestCase):
    def test_period_comparison_preserves_phase_numbers(self):
        observation = execute_intent(
            {
                "action": "compare_periods",
                "metric_id": "paid_revenue",
                "baseline": "Q1",
                "focus": "Q2",
                "group_by": None,
                "filters": {},
                "semantic_version": "1.1",
            }
        )
        self.assertEqual(observation["baseline_value"], 270)
        self.assertEqual(observation["focus_value"], 200)
        self.assertEqual(observation["delta"], -70)

    def test_region_breakdown_reconciles_with_total_delta(self):
        observation = execute_intent(
            {
                "action": "breakdown_delta",
                "metric_id": "paid_revenue",
                "baseline": "Q1",
                "focus": "Q2",
                "group_by": "region",
                "filters": {},
                "semantic_version": "1.1",
            }
        )
        deltas = {row["segment"]: row["delta"] for row in observation["segments"]}
        self.assertEqual(deltas, {"Казань": 0, "Москва": -20, "Питер": -50})
        self.assertEqual(sum(deltas.values()), observation["delta"])

    def test_full_investigation_chooses_piter_then_pro(self):
        result = investigate(QUESTION)
        self.assertEqual(result["status"], "ready_for_review")
        self.assertEqual(
            [step["intent"]["action"] for step in result["trace"]],
            ["compare_periods", "breakdown_delta", "breakdown_delta"],
        )
        self.assertEqual(result["trace"][1]["intent"]["group_by"], "region")
        self.assertEqual(result["trace"][2]["intent"]["group_by"], "product")
        self.assertEqual(result["trace"][2]["intent"]["filters"], {"region": "Питер"})
        self.assertEqual(
            result["finding"]["path"],
            [
                {"dimension": "region", "segment": "Питер", "delta": -50},
                {"dimension": "product", "segment": "Pro", "delta": -40},
            ],
        )

    def test_largest_current_segment_is_not_confused_with_largest_drop(self):
        result = investigate(QUESTION)
        region_observation = result["trace"][1]["observation"]
        q2_values = {
            row["segment"]: row["focus_value"]
            for row in region_observation["segments"]
        }
        self.assertEqual(max(q2_values, key=q2_values.get), "Москва")
        self.assertEqual(result["finding"]["path"][0]["segment"], "Питер")

    def test_no_decline_stops_after_comparison(self):
        def no_decline_executor(intent):
            return {
                "kind": "period_comparison",
                "metric_id": "paid_revenue",
                "baseline": "Q1",
                "focus": "Q2",
                "baseline_value": 270,
                "focus_value": 280,
                "delta": 10,
                "unit": "RUB",
                "filters": {},
                "semantic_version": intent["semantic_version"],
            }

        result = investigate(QUESTION, executor=no_decline_executor)
        self.assertEqual(result["status"], "premise_not_supported")
        self.assertEqual(len(result["trace"]), 1)

    def test_unknown_metric_is_rejected_before_execution(self):
        with self.assertRaisesRegex(ValueError, "unknown metric_id"):
            investigate(QUESTION, metric_id="gross_revenue")

    def test_unknown_dimension_is_rejected_by_executor(self):
        with self.assertRaisesRegex(ValueError, "unknown group_by dimension"):
            execute_intent(
                {
                    "action": "breakdown_delta",
                    "metric_id": "paid_revenue",
                    "baseline": "Q1",
                    "focus": "Q2",
                    "group_by": "manager_email",
                    "filters": {},
                    "semantic_version": "1.1",
                }
            )

    def test_step_budget_stops_before_unapproved_extra_query(self):
        result = investigate(QUESTION, max_steps=2)
        self.assertEqual(result["status"], "step_budget_exhausted")
        self.assertEqual(len(result["trace"]), 2)

    def test_empty_breakdown_stops_as_insufficient_data(self):
        comparison = execute_intent(
            {
                "action": "compare_periods",
                "metric_id": "paid_revenue",
                "baseline": "Q1",
                "focus": "Q2",
                "group_by": None,
                "filters": {},
                "semantic_version": "1.1",
            }
        )
        state = {
            "question": QUESTION,
            "metric_id": "paid_revenue",
            "baseline": "Q1",
            "focus": "Q2",
            "semantic_version": "1.1",
        }
        empty = {
            "kind": "delta_breakdown",
            "metric_id": "paid_revenue",
            "baseline": "Q1",
            "focus": "Q2",
            "baseline_value": 0,
            "focus_value": 0,
            "delta": 0,
            "unit": "RUB",
            "filters": {},
            "semantic_version": "1.1",
            "group_by": "region",
            "segments": [],
        }
        trace = [
            {"intent": {}, "observation": comparison},
            {"intent": {"group_by": "region", "filters": {}}, "observation": empty},
        ]
        decision = choose_next_action(state, trace, SEMANTIC)
        self.assertEqual(decision["status"], "insufficient_data")

    def test_mismatched_segment_sum_stops_investigation(self):
        calls = 0

        def inconsistent_executor(intent):
            nonlocal calls
            calls += 1
            if calls == 1:
                return execute_intent(intent)
            observation = execute_intent(intent)
            observation["segments"][0]["delta"] = 10
            return observation

        result = investigate(QUESTION, executor=inconsistent_executor)
        self.assertEqual(result["status"], "observation_mismatch")
        self.assertEqual(len(result["trace"]), 2)

    def test_trace_keeps_semantic_version_and_policy_reason(self):
        result = investigate(QUESTION)
        for step in result["trace"]:
            self.assertEqual(step["intent"]["semantic_version"], "1.1")
            self.assertEqual(step["observation"]["semantic_version"], "1.1")
            self.assertTrue(step["policy_reason"])


if __name__ == "__main__":
    unittest.main()
