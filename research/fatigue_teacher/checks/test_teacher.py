from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import unittest
import numpy as np
from research.fatigue_mechanism.checks.test_core import make_instance
from research.fatigue_mechanism.model import Genome, FatigueParams
from research.fatigue_mechanism.decoder import decode
from research.fatigue_mechanism.instances import parent_genome
from research.fatigue_mechanism.prediction import prepare_defects
from ..protocol import PROTOCOL, selected_instances
from ..teachers import Teacher, build_bank
from ..candidates import Candidate, make_pool, inherit, physical_signature
from ..chain import run
from ..audit import check
from ..validation import verify_pool
from ..statistics import paired, adjust_primary
from .. import scoring


class TeacherChecks(unittest.TestCase):
    def setUp(self):
        self.instance = make_instance(np.random.default_rng(321), jobs=20, stages=3)
        self.receiver = parent_genome(self.instance, 23)
        self.params = FatigueParams(.1, .08, .7, .2)
        self.parent = decode(self.instance, self.receiver, self.params)
        self.weights = [0., 1., 0.]
        self.teachers, _ = build_bank(self.instance, self.params, self.receiver,
                                    np.asarray(self.weights)/self.parent.objectives, 997, "fixed_FA")
        self.seeds = {"bank": 997, "pool": 337, "choice": 113}

    def test_inheritance_only_changes_block_and_moves_job_owned_tuples(self):
        block = (0, 2, 4)
        donor = self.teachers[0]
        child = inherit(self.receiver, donor, block, True)
        for p, job in enumerate(self.receiver.js):
            if job not in block:
                self.assertEqual(child.js[p], job)
                self.assertEqual(child.by_job()[job], self.receiver.by_job()[job])
        for job in block:
            self.assertEqual(child.by_job()[job], donor.genome.by_job()[job])

    def test_neutral_global_interleaving_dropped_without_truth(self):
        attrs = self.receiver.by_job()
        js = [j for f in range(self.instance.factories) for j in self.receiver.js if attrs[j][0] == f]
        teacher = Teacher(0, Genome.from_job_attributes(js, attrs), (1., 1., 1.), .8)
        # All jobs makes this a pure global interleaving. A partial block can
        # change its position relative to unselected jobs in the same factory.
        pool, metadata = make_pool(self.instance, self.receiver, (teacher, teacher), 337, 20, "fixed_FA")
        self.assertTrue(metadata["fallback_noop"])
        self.assertEqual(metadata["unchanged"], 4)
        self.assertEqual(pool[0].genome, self.receiver)

    def test_duplicate_candidates_retain_both_teacher_origins(self):
        attrs = {j: (f, (m+1) % 3, w) for j, (f, m, w) in self.receiver.by_job().items()}
        genome = Genome.from_job_attributes(self.receiver.js, attrs)
        a, b = Teacher(0, genome, (1., 1., 1.), .8), Teacher(1, genome, (1., 1., 1.), .9)
        pool, metadata = make_pool(self.instance, self.receiver, (a, b), 337, 2, "fixed_FA")
        self.assertEqual(len(pool), 1)
        self.assertEqual(len(pool[0].origins), 2)
        self.assertEqual(metadata["duplicates"], 1)

    def test_empty_factory_transfer_rejected_with_explicit_noop(self):
        block = tuple(map(int, np.random.default_rng(337).choice(20, 2, replace=False)))
        source_job = next(j for j in range(20) if j not in block)
        attrs = {j: (0 if j == block[0] else 1, 0, 0) for j in range(20)}
        receiver = Genome.from_job_attributes(range(20), attrs)
        donor_attrs = {j: (0 if j == source_job else 1, 0, 0) for j in range(20)}
        donor = Teacher(0, Genome.from_job_attributes(range(20), donor_attrs), (1., 1., 1.), .8)
        pool, metadata = make_pool(self.instance, receiver, (donor, donor), 337, 2, "transfer_FA")
        self.assertEqual(metadata["illegal"], 2)
        self.assertTrue(metadata["fallback_noop"])

    def test_fixed_and_transfer_numerical_gate(self):
        for regime in PROTOCOL["regimes"]:
            result = verify_pool(self.instance, self.params, self.receiver, 337, regime, 6)
            self.assertGreaterEqual(result["candidates"], 1)

    def test_beta_zero_boundaries_agree_and_cache_rejects_wrong_version(self):
        params = FatigueParams(.1, .08, 0., .2)
        parent = decode(self.instance, self.receiver, params)
        pool, _ = make_pool(self.instance, self.receiver, self.teachers, 337, 6, "fixed_FA")
        values = []
        for method in ("time", "fatigue"):
            cache = scoring.build(self.instance, params, self.receiver, parent, method, "fixed_FA", self.weights, parent.objectives, 0)
            values.append(scoring.scores(self.instance, params, self.receiver, parent, pool, self.teachers, cache, method, "fixed_FA", 0)[0])
            with self.assertRaises(AssertionError):
                scoring.scores(self.instance, params, self.receiver, parent, pool, self.teachers, cache, method, "fixed_FA", 1)
        np.testing.assert_allclose(values[0], values[1], atol=1e-13, rtol=0)

    def test_cheap_does_not_truncate_more_than16_defects(self):
        attrs = {j: (f, (m+1) % 3, w) for j, (f, m, w) in self.receiver.by_job().items()}
        candidate = Candidate("teacher", "joint", Genome.from_job_attributes(self.receiver.js[::-1], attrs), tuple(range(20)), ((0, "joint"),))
        with self.assertRaises(ValueError):
            prepare_defects(self.instance, self.params, self.parent, [candidate])
        cache = scoring.build(self.instance, self.params, self.receiver, self.parent, "cheap", "fixed_FA", self.weights, self.parent.objectives, 0)
        scores, calls, _ = scoring.scores(self.instance, self.params, self.receiver, self.parent, [candidate], self.teachers, cache, "cheap", "fixed_FA", 0)
        self.assertTrue(np.isfinite(scores).all())
        self.assertEqual(calls, 0)

    def test_snapshot_same_pool_and_independent_full_call_accounting(self):
        previous = None
        for method in PROTOCOL["methods"]:
            identity = {"method": method, "mode": "snapshot", "regime": "fixed_FA", "block_size": 2}
            with patch("research.fatigue_teacher.chain.decode", wraps=decode) as recipient_calls, patch("research.fatigue_teacher.teachers.decode", wraps=decode) as bank_calls:
                result, rows, epochs = run(self.instance, self.params, self.receiver, self.weights, identity, self.seeds)
            self.assertEqual(recipient_calls.call_count+bank_calls.call_count, 10)
            check(self.instance, self.params, self.receiver, self.weights, result, rows, epochs)
            context = (result["teacher_bank"], rows[0]["pool_metadata"])
            if previous is not None:
                self.assertEqual(context, previous)
            previous = context

    def test_fixed24_counts_and_zero_time_setup_is_paid(self):
        identity = {"method": "time", "mode": "steps", "regime": "fixed_FA", "block_size": 2}
        result, rows, epochs = run(self.instance, self.params, self.receiver, self.weights, identity, self.seeds)
        self.assertEqual(result["full_decodes"], 33)
        check(self.instance, self.params, self.receiver, self.weights, result, rows, epochs)
        protocol = deepcopy(PROTOCOL)
        protocol["time_budget_seconds"] = 0.
        result, rows, epochs = run(self.instance, self.params, self.receiver, self.weights, {**identity, "mode": "time"}, self.seeds, protocol)
        self.assertEqual(result["full_decodes"], 9)
        self.assertEqual(result["gain"], 0.)
        self.assertGreater(result["overrun_ns"], 0)
        check(self.instance, self.params, self.receiver, self.weights, result, rows, epochs, protocol)

    def test_design_and_exact_paired_statistics(self):
        project = Path(__file__).resolve().parents[3]
        names = selected_instances(project)
        self.assertEqual(len(names), 13)
        self.assertEqual(len({tuple(map(int, n.split("_")[:2])) for n in names}), 13)
        self.assertEqual(13*5*2*2*20, PROTOCOL["expected_total_runs"])
        rows = [{"instance": i, "parent_seed": seed, "method": m, "gain": v}
                for i in ("a", "b") for seed in PROTOCOL["parent_seeds"] for m, v in (("time", .2), ("direct", .1))]
        result = paired(rows, "time", "direct")
        self.assertEqual(result["exact_one_sided_p"], .25)
        self.assertEqual(result["instances"], 2)
        np.testing.assert_allclose(result["bootstrap_95_interval"], [.1, .1])
        family = [{"mode": mode, "target": "TEC", "regime": "fixed_FA", "block_size": 2,
                   "left": a, "right": b, "exact_one_sided_p": .001, "bootstrap_95_interval": [.1, .2]}
                  for mode in ("snapshot", "steps", "time") for a, b in PROTOCOL["primary"]["comparisons"]]
        self.assertEqual(len(adjust_primary(family)), 12)
        self.assertTrue(all(r["primary_supported"] for r in family))


if __name__ == "__main__":
    unittest.main()
