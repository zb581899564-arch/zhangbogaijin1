"""Focused mathematical/schema checks; no scheduler, JVM or new experiments."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from .analysis import analyse
from .kernel_metrics import KERNELS, case_metrics, paired_contrasts, validate_pairing
from .retention import batch_metrics, generation_metrics, retention_gate, validate_generations

NORMALIZATION = {"lower": [0., 0., 0.], "scale": [1., 1., 1.]}


def solution(value, gene=0):
    return {"JS": [0], "FA": [gene], "MA": [0], "WA": [0], "objectives": [value] * 3}


def generation():
    # The parent is better than every new G/L candidate, while every G/L ND
    # objective survives selection. The previous pool-only diagnostic misses P.
    return {"type": "generation", "generation": 1, "elapsedSeconds": .5,
            "successfulFE": 200, "deadlineValid": True, "complete": True,
            "parents": [solution(.2)], "global": [solution(.6, 1)],
            "local": [solution(.5, 2)], "selected": [solution(.5, 2)]}


def kernel_case(kernel="PAPER", rep=0):
    return {"instance": "tiny", "origin": "SO", "phase": "early", "caseId": "case-1",
            "kernel": kernel, "rep": rep, "seed": 123 + rep, "successfulFE": 1,
            "reference": [[.5, .5, .5]], "parent": solution(.5), "personal": solution(.5),
            "global": solution(.4, 1), "child": solution(.6, 2),
            "generationNanos": 100, "evaluationNanos": 200, "repairChanged": False,
            "changesByJob": {"FA": 1}}


class MechanismChecks(unittest.TestCase):
    def test_parent_elite_loss_can_coexist_with_complete_GL_ND_retention(self):
        row = generation_metrics(generation(), NORMALIZATION)
        self.assertEqual(row["GLNDCoveredBySelectedFraction"], 1.)
        self.assertEqual(row["GLHVMinusSelectedHV"], 0.)
        self.assertEqual(row["parentNDUncoveredByGLFraction"], 1.)
        self.assertEqual(row["parentNDGenotypeSurvivalSelectedFraction"], 0.)
        self.assertAlmostEqual(row["offlineOracleParentGainHV"], 1.3 ** 3 - 1.)

    def test_objective_coverage_and_exact_genotype_survival_are_distinct(self):
        record = generation()
        record["global"] = [solution(.2, 3)]
        record["selected"] = [solution(.2, 3)]
        row = generation_metrics(record, NORMALIZATION)
        self.assertEqual(row["parentNDCoveredByGLFraction"], 1.)
        self.assertEqual(row["parentNDStrictlyDominatedByGLFraction"], 0.)
        self.assertEqual(row["parentNDGenotypeSurvivalGLFraction"], 0.)
        self.assertEqual(row["offlineOracleParentGainHV"], 0.)

    def test_minimization_direction_and_zero_HV_gain(self):
        record = kernel_case()
        worse = case_metrics(record, NORMALIZATION)
        self.assertEqual(worse["candidateDeltaHV"], 0.)
        self.assertTrue(worse["candidateDominatedByParent"])
        self.assertFalse(worse["candidateDominatesParent"])
        record["child"] = solution(.4, 2)
        better = case_metrics(record, NORMALIZATION)
        self.assertAlmostEqual(better["candidateDeltaHV"], 1.1 ** 3 - 1.)
        self.assertTrue(better["candidateDominatesParent"])
        self.assertFalse(better["candidateDominatedByParent"])

    def test_candidate_and_paid_batch_increment_are_separate(self):
        record = kernel_case()
        record["children"] = [record["child"], solution(.4, 3)]
        row = case_metrics(record, NORMALIZATION)
        self.assertEqual(row["candidateDeltaHV"], 0.)
        self.assertGreater(row["batchDeltaHV"], 0.)
        self.assertEqual(row["paidBatchSize"], 2)
        self.assertAlmostEqual(row["generationEvaluationSeconds"], 3e-7)

    def test_pairing_rejects_missing_replicates_duplicates_and_changed_parent(self):
        rows = [kernel_case(kernel, rep) for kernel in KERNELS for rep in range(2)]
        self.assertEqual(len(validate_pairing(rows, 2)), 1)
        self.assertEqual(len(paired_contrasts([case_metrics(row, NORMALIZATION) for row in rows])), 6)
        for malformed in (rows[:-1], rows + [rows[0]]):
            with self.assertRaises(ValueError):
                validate_pairing(malformed, 2)
        changed = copy.deepcopy(rows)
        changed[-1]["parent"] = solution(.3)
        with self.assertRaises(ValueError):
            validate_pairing(changed, 2)
        # A whole missing case is rejected against the captured case registry.
        with self.assertRaises(ValueError):
            validate_pairing(rows, 2, expected_cases={("tiny", "SO", "early", "case-2")})

    def test_partial_generation_is_excluded_and_future_is_rejected(self):
        partial = {"type": "generation", "complete": False, "parents": None, "successfulFE": None}
        self.assertEqual(len(validate_generations([generation(), partial], 1.)), 1)
        future = generation() | {"elapsedSeconds": 1.1}
        with self.assertRaises(ValueError):
            validate_generations([future], 1.)

    def test_gate_gives_equal_weight_to_instances_and_requires_four_positive(self):
        rows = []
        instances = ["i" + str(index) for index in range(6)]
        for variant in ("SO", "SHARE"):
            for index, instance in enumerate(instances):
                for seed in range(3):
                    rows.append({"instance": instance, "seed": seed, "variant": variant,
                                 "offlineOracleParentGainPercentOfGL": 2. if index < 4 else 0.})
        gate = retention_gate(rows, instances)
        self.assertTrue(gate["triggered"])
        self.assertAlmostEqual(gate["variants"]["SO"]["meanOracleParentGainPercentOfGL"], 4 / 3)
        insufficient = [row | {"offlineOracleParentGainPercentOfGL": 10. if row["instance"] in instances[:3] else 0.}
                        for row in rows]
        self.assertFalse(retention_gate(insufficient, instances)["triggered"])

    def test_direction_batch_uses_same_parent_reference(self):
        record = generation()
        record["batches"] = [{"direction": 0, "step": step, "successfulFE": 100 + step,
                               "elapsedSeconds": .1, "objectives": [[value] * 3]}
                              for step, value in ((1, .6), (10, .1))]
        rows = batch_metrics(record, NORMALIZATION)
        self.assertEqual(rows[0]["parentReferenceHV"], rows[1]["parentReferenceHV"])
        self.assertEqual(rows[0]["batchDeltaHVAgainstFixedParents"], 0.)
        self.assertGreater(rows[1]["batchDeltaHVAgainstFixedParents"], 0.)

    def test_missing_trial_fails_before_creating_analysis_directory(self):
        protocol = {"instances": [{"stem": "tiny", "time_seconds": 1., "normalization": NORMALIZATION}],
                    "algorithm_seeds": [1], "phases": {"diagnostics": ["SO", "SHARE", "NSGA"]},
                    "variants": {label: {} for label in ("SO", "SHARE", "NSGA")}}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(FileNotFoundError):
                analyse(root, protocol)
            self.assertFalse((root / "analysis").exists())


if __name__ == "__main__":
    unittest.main()
