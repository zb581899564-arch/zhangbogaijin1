"""Synthetic mathematical/protocol checks only; no scheduler, FE or JVM."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np

from research.dynamic_benchmark.metrics import check_metrics, hypervolume, igd_plus, nondominated
from .analysis import analyze
from .diagnostics import validate_trace
from .evidence import read, status, write_once
from .execution import command, controller_lock, run_one
from .metrics import comparisons, interaction
from .protocol import PREVIOUS, VARIANTS, jobs, make_protocol
from .trials import normalized_front


def synthetic_records(protocol):
    values = {"V2": 100., "S_ONLY": 110., "O_ONLY": 120., "SO": 150.,
              "NSGA2_CONTROL": 130., "SYNC_FIX": 145., "SHARE_FIX": 155.}
    return [{"instance": instance["stem"], "seed": seed, "variant": label,
             "hv": {str(ref): values[label] for ref in (1.25, 1.5, 2.0)},
             "hv_half": values[label] / 2, "hv_fe15000": values[label], "igdplus": 1.}
            for instance in protocol["instances"] for seed in protocol["algorithm_seeds"] for label in VARIANTS]


class RepairChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous = read(PREVIOUS / "protocol.json")
        cls.protocol = make_protocol(cls.previous)

    def test_authorized_matrix_copies_numerical_constants_and_balanced_phases(self):
        self.assertEqual(self.protocol["instances"], self.previous["instances"])
        self.assertEqual(self.protocol["algorithm_seeds"], self.previous["algorithm_seeds"])
        self.assertEqual(len(jobs(self.protocol, "factorial")), 150)
        self.assertEqual(len(jobs(self.protocol, "cooperation")), 60)
        self.assertEqual(self.protocol["planned_search_seconds"], 1820)
        self.assertEqual(self.protocol["fixed_repaired_baseline"], "SO")
        self.assertNotIn("green_all_required", self.protocol)

    def test_frozen_order_is_deterministic_and_each_cell_occurs_once(self):
        for phase in ("factorial", "cooperation"):
            order = jobs(self.protocol, phase)
            self.assertEqual(order, jobs(copy.deepcopy(self.protocol), phase))
            cells = {(row["instance"], row["seed"], row["variant"]) for row in order}
            self.assertEqual(len(cells), len(order))

    def test_java_parameter_contract_unchanged_through_argument14(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "classpath.txt").write_text("frozen-classes", encoding="utf-8")
            job = jobs(self.protocol, "cooperation")[0]
            spec = self.protocol["variants"][job["variant"]]
            cmd = command(root, root / "trial", job, spec)
            args = cmd[cmd.index("research.dynamic.DynamicRun") + 1:]
            self.assertEqual(len(args), 17)
            self.assertEqual(args[9:15], ["true", "false", "0", "true", "SCREEN", "0"])
            self.assertEqual(args[15:], ["SO", "true"])
            self.assertEqual(args[4], spec["mode"])

    def test_factorial_interaction_uses_common_v2_denominator(self):
        records = synthetic_records(self.protocol)
        index = {(r["instance"], r["seed"], r["variant"]): r for r in records}
        result = interaction(index, [row["stem"] for row in self.protocol["instances"]], self.protocol["algorithm_seeds"])
        self.assertEqual(result["mean_interaction_percent"], 20.)
        for row in result["instances"]:
            self.assertEqual(row["mean_interaction_hv"], 20.)
            self.assertEqual(row["paired_seeds"][0]["interaction_percent_of_paired_V2"], 20.)
        # Percentages with different comparator denominators are not subtracted.
        self.assertNotEqual(100 * (150 / 110 - 1) - 100 * (120 / 100 - 1), 20.)

    def test_seed_outlier_does_not_create_practical_instance_win(self):
        records = synthetic_records(self.protocol)
        for row in records:
            if row["variant"] == "S_ONLY":
                value = 130. if row["seed"] == self.protocol["algorithm_seeds"][0] else 99.
                row["hv"] = {key: value for key in row["hv"]}
        result = comparisons(records, self.protocol)["comparisons"]["S_ONLY__vs__V2"]["final"]["1.5"]
        self.assertGreater(result["mean_effect_percent"], 1.)
        self.assertEqual(result["practical_wins"], 0)

    def test_fe_censoring_is_not_imputed_or_mixed_with_full_matrix_mean(self):
        records = synthetic_records(self.protocol)
        first = self.protocol["instances"][0]["stem"]
        next(row for row in records if row["instance"] == first and row["variant"] == "SO")["hv_fe15000"] = None
        result = comparisons(records, self.protocol)["comparisons"]["SO__vs__V2"]["FE15000"]
        self.assertIsNone(result["all_instances"]["mean_effect_percent"])
        self.assertEqual(result["complete_pairs_only"]["complete_pair_instances"], 5)
        self.assertEqual(result["complete_pairs_only"]["mean_effect_percent"], 50.)

    def test_zero_denominator_stays_unresolved(self):
        records = synthetic_records(self.protocol)
        for row in records:
            if row["variant"] == "V2":
                row["hv"] = {key: 0. for key in row["hv"]}
        result = comparisons(records, self.protocol)
        self.assertIsNone(result["comparisons"]["SO__vs__V2"]["final"]["1.5"]["mean_effect_percent"])
        self.assertIsNone(result["factorial_interactions"]["1.5"]["mean_interaction_percent"])
        json.dumps(result, allow_nan=False)

    def test_exact_hv_igd_and_full_union_reference(self):
        check_metrics()
        self.assertAlmostEqual(hypervolume([[.5, .5, .5]], [1.5] * 3), 1.)
        reference = nondominated([[.5, .5, .5], [.4, .4, .4], [.6, .6, .6]])
        self.assertEqual(reference.tolist(), [[.4, .4, .4]])
        self.assertGreater(igd_plus([[.5, .5, .5]], reference), 0.)
        self.assertEqual(igd_plus([[.4, .4, .4]], reference), 0.)

    def test_normalization_and_deadline_guard(self):
        point = {"front": [[3., 5., 7.]], "elapsedSeconds": .9, "reached": True}
        result = normalized_front(point, 1., np.array([1., 1., 1.]), np.array([2., 4., 6.]))
        self.assertEqual(result.tolist(), [[1., 1., 1.]])
        with self.assertRaises(ValueError):
            normalized_front(point, .8, np.zeros(3), np.ones(3))
        self.assertIsNone(normalized_front({"front": [], "reached": False}, 1., np.zeros(3), np.ones(3)))
        with self.assertRaises(ValueError):
            normalized_front({"front": [[1, 1, 1]], "reached": False}, 1., np.zeros(3), np.ones(3))

    def test_trace_summary_must_match_and_remain_bounded(self):
        audit = {"paidEvaluationsObserved": 10, "paidArchiveAdmissions": 2,
                 "globalSampledPaid": 1, "globalSampledDifferent": 1,
                 "poolsObserved": 0, "poolsCaptured": 0, "auditSeconds": .001,
                 "poolCapturePolicy": "first2+last"}
        validate_trace([{"type": "audit-summary", **audit}], audit, {"successful": 10})
        changed = {**audit, "auditSeconds": .002}
        with self.assertRaises(ValueError):
            validate_trace([{"type": "audit-summary", **changed}], audit, {"successful": 10})
        overflow = {**audit, "poolsCaptured": 4}
        with self.assertRaises(ValueError):
            validate_trace([{"type": "audit-summary", **overflow}] + [{"type": "pool"}] * 4,
                           overflow, {"successful": 10})

    def test_status_event_survives_windows_projection_lock(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(Path, "replace", side_effect=PermissionError("synthetic locked reader")), patch("time.sleep"):
                status(root, {"status": "RUNNING", "completed": 1})
            events = list((root / "status-events").glob("*.json"))
            self.assertEqual(len(events), 1)
            self.assertEqual(read(events[0])["completed"], 1)

    def test_second_controller_cannot_acquire_active_owner(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with controller_lock(root):
                with self.assertRaises(RuntimeError):
                    with controller_lock(root):
                        self.fail("Concurrent campaign owner was allowed")

    def test_incomplete_owner_is_preserved_without_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "classpath.txt").write_text("frozen", encoding="utf-8")
            folder = root / "trial"
            folder.mkdir()
            with patch("subprocess.run") as dispatch:
                with self.assertRaises(RuntimeError):
                    run_one(root, folder, jobs(self.protocol, "factorial")[0], self.protocol["instances"][0],
                            self.protocol["variants"]["V2"], None)
                dispatch.assert_not_called()
            self.assertTrue(folder.exists())

    def test_full_offline_report_uses_all_seven_and_never_overwrites(self):
        points = {label: .9 - .05 * index for index, label in enumerate(VARIANTS)}
        runs = []
        for record in synthetic_records(self.protocol):
            audit = {"auditSeconds": .001, "poolExportSeconds": .002,
                     "globalSampledPaid": 2, "globalSampledDifferent": 1}
            summary = {"attempted": 15000, "successful": 15000, "searchSeconds": 1.,
                       "deadlineOvershootSeconds": .001, "timeInterruptedAttempts": 0,
                       "archiveSize": 1, "offlineValidationDecodes": 1, "semanticAudit": audit,
                       "semanticProfile": VARIANTS[record["variant"]]["profile"], "classicSetting": 0}
            front = np.array([[points[record["variant"]]] * 3])
            runs.append({key: record[key] for key in ("instance", "seed", "variant")}
                        | {"summary": summary, "final": front, "half": front, "fe": front,
                           "finalRow": {"fe": 15000}, "halfRow": {"fe": 10000},
                           "traceSummary": {"rows": 1, "types": {"audit-summary": 1},
                                            "deadlineValidPools": 0, "deadlineInvalidPools": 0}})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_once(root / "protocol.json", self.protocol)
            with patch("research.semantic_repair.analysis._load_runs", return_value=runs):
                output = analyze(root)
                before = (output / "report.md").read_bytes()
                second = analyze(root)
            self.assertNotEqual(output, second)
            self.assertEqual((output / "report.md").read_bytes(), before)
            self.assertEqual(len(read(output / "records.json")), 210)
            reference = read(output / (self.protocol["instances"][0]["stem"] + "-reference.json"))
            np.testing.assert_allclose(reference, [[points["SHARE_FIX"]] * 3])
            self.assertEqual(read(output / "audit.json")["runs"], 210)


def run_checks():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RepairChecks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("SEMANTIC_SYNTHETIC_CHECKS_PASS", result.testsRun, "no JVM/search/FE", flush=True)


if __name__ == "__main__":
    run_checks()
