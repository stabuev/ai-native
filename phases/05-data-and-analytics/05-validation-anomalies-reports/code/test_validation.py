import math
import unittest
from copy import deepcopy

from validation import (
    DEMO_INVESTIGATION,
    DEMO_PACKET,
    DEMO_POLICY,
    DEMO_SEMANTIC,
    build_validation_packet,
    detect_current_anomaly,
    run_quality_gate,
)


def failed_ids(result):
    return {check["id"] for check in result["checks"] if not check["passed"]}


class QualityGateTests(unittest.TestCase):
    def test_investigation_trace_builds_reference_packet(self):
        packet = build_validation_packet(
            deepcopy(DEMO_INVESTIGATION),
            deepcopy(DEMO_SEMANTIC),
            run_id=DEMO_PACKET["run_id"],
            as_of=DEMO_PACKET["as_of"],
            history=deepcopy(DEMO_PACKET["history"]),
        )

        self.assertEqual(packet, DEMO_PACKET)
        self.assertEqual(run_quality_gate(packet)["decision"], "publish")

    def test_unfinished_investigation_cannot_publish(self):
        investigation = deepcopy(DEMO_INVESTIGATION)
        investigation["status"] = "step_budget_exhausted"
        investigation["trace"] = investigation["trace"][:2]
        investigation["finding"] = None
        packet = build_validation_packet(
            investigation,
            deepcopy(DEMO_SEMANTIC),
            run_id="unfinished-run",
            as_of=DEMO_PACKET["as_of"],
            history=deepcopy(DEMO_PACKET["history"]),
        )

        result = run_quality_gate(packet)

        self.assertEqual(result["decision"], "block")
        self.assertIn("trace.ready_for_review", failed_ids(result))

    def test_reference_packet_is_publishable(self):
        result = run_quality_gate(deepcopy(DEMO_PACKET))

        self.assertEqual(result["decision"], "publish")
        self.assertEqual(result["anomaly"]["status"], "clear")
        self.assertFalse(failed_ids(result))

    def test_unusual_current_value_requires_review(self):
        packet = deepcopy(DEMO_PACKET)
        packet["history"][:-1] = [
            {"period": f"baseline-{index}", "value": value}
            for index, value in enumerate([268, 272, 269, 271, 270], start=1)
        ]

        result = run_quality_gate(packet)

        self.assertEqual(result["decision"], "review")
        self.assertEqual(result["anomaly"]["status"], "review")
        self.assertGreater(abs(result["anomaly"]["z"]), 2.0)

    def test_insufficient_history_is_not_reported_as_clear(self):
        packet = deepcopy(DEMO_PACKET)
        packet["history"] = packet["history"][-3:]

        result = run_quality_gate(packet)

        self.assertEqual(result["decision"], "review")
        self.assertEqual(result["anomaly"]["status"], "insufficient_history")

    def test_semantic_version_mismatch_blocks_release(self):
        packet = deepcopy(DEMO_PACKET)
        packet["semantic_version"] = "0.9"

        result = run_quality_gate(packet)

        self.assertEqual(result["decision"], "block")
        self.assertIn("contract.semantic_version", failed_ids(result))

    def test_missing_required_filter_blocks_release(self):
        packet = deepcopy(DEMO_PACKET)
        packet["filters"] = {}

        result = run_quality_gate(packet)

        self.assertEqual(result["decision"], "block")
        self.assertIn("contract.required_filters", failed_ids(result))

    def test_wrong_focus_control_value_blocks_release(self):
        packet = deepcopy(DEMO_PACKET)
        packet["totals"]["Q2"] = 201.0
        packet["history"][-1]["value"] = 201.0

        result = run_quality_gate(packet)

        self.assertEqual(result["decision"], "block")
        self.assertIn("totals.focus_control", failed_ids(result))

    def test_missing_region_blocks_release(self):
        packet = deepcopy(DEMO_PACKET)
        packet["breakdowns"]["region"].pop()

        result = run_quality_gate(packet)

        self.assertEqual(result["decision"], "block")
        self.assertIn("region.segments", failed_ids(result))

    def test_wrong_row_delta_blocks_release(self):
        packet = deepcopy(DEMO_PACKET)
        packet["breakdowns"]["region"][0]["delta"] = -19.0

        result = run_quality_gate(packet)

        self.assertEqual(result["decision"], "block")
        self.assertIn("region.row_arithmetic", failed_ids(result))
        self.assertIn("region.reconciliation", failed_ids(result))

    def test_product_contributions_must_match_piter_delta(self):
        packet = deepcopy(DEMO_PACKET)
        packet["breakdowns"]["product|region=Питер"][1].update(
            {"focus_value": 20.0, "delta": -30.0}
        )

        result = run_quality_gate(packet)

        self.assertEqual(result["decision"], "block")
        self.assertIn(
            "product|region=Питер.reconciliation", failed_ids(result)
        )

    def test_non_finite_total_blocks_release(self):
        packet = deepcopy(DEMO_PACKET)
        packet["totals"]["Q2"] = math.nan

        result = run_quality_gate(packet)

        self.assertEqual(result["decision"], "block")
        self.assertIn("totals.finite", failed_ids(result))

    def test_evidence_path_must_be_supported(self):
        cases = {
            "unsupported step": [
                DEMO_PACKET["evidence_path"][0],
                {
                    **DEMO_PACKET["evidence_path"][1],
                    "delta": -999.0,
                },
            ],
            "empty path": [],
        }
        for case, evidence_path in cases.items():
            with self.subTest(case=case):
                packet = deepcopy(DEMO_PACKET)
                packet["evidence_path"] = deepcopy(evidence_path)

                result = run_quality_gate(packet)

                self.assertEqual(result["decision"], "block")
                self.assertIn("evidence_path.supported", failed_ids(result))

    def test_invalid_history_blocks_release(self):
        packet = deepcopy(DEMO_PACKET)
        packet["history"][2]["value"] = "unknown"

        result = run_quality_gate(packet)

        self.assertEqual(result["decision"], "block")
        self.assertEqual(result["anomaly"]["status"], "invalid")

    def test_change_from_constant_baseline_requires_review(self):
        anomaly = detect_current_anomaly(
            [
                {"period": "p1", "value": 100},
                {"period": "p2", "value": 100},
                {"period": "p3", "value": 100},
                {"period": "p4", "value": 100},
                {"period": "p5", "value": 100},
                {"period": "current", "value": 120},
            ]
        )

        self.assertEqual(anomaly["status"], "review")
        self.assertIsNone(anomaly["z"])

    def test_report_contains_decision_failures_and_evidence_boundary(self):
        packet = deepcopy(DEMO_PACKET)
        packet["filters"] = {}

        result = run_quality_gate(packet)
        report = result["report"]

        self.assertIn("Решение: **block**", report)
        self.assertIn("[FAIL] `contract.required_filters`", report)
        self.assertIn("region=Питер", report)
        self.assertIn("не доказывает его причину", report)


if __name__ == "__main__":
    unittest.main()
