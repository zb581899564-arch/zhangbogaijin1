from copy import deepcopy
from dataclasses import replace
import unittest
from unittest.mock import patch
import numpy as np
from research.fatigue_mechanism.checks.test_core import make_instance
from research.fatigue_mechanism.instances import parent_genome
from research.fatigue_mechanism.model import FatigueParams
from research.fatigue_mechanism.decoder import decode
from research.fatigue_topology.trials import local_pool as reference_pool
from research.fatigue_topology.counterfactual import stage0, boundary_costates, cut_prediction
from ..neighbors import local_pool
from ..stage0 import exact_stage0
from ..scorer import build, scores
from ..chain import run
from ..protocol import PROTOCOL
from ..audit import audit_chain
from ..summary import paired


class ReuseChecks(unittest.TestCase):
    def setUp(self):
        self.instance = make_instance(np.random.default_rng(99139), jobs=20, stages=3)
        self.genome = parent_genome(self.instance, 17)
        self.params = FatigueParams(.1, .08, .7)
        self.parent = decode(self.instance, self.genome, self.params)
        self.pool = local_pool(self.instance, self.genome, 839)
        self.protocol = deepcopy(PROTOCOL)
        self.protocol["decisions"] = 6

    def test_descriptor_pool_is_exact_reference_stream(self):
        for seed in (1, 7, 83, 839, 991):
            self.assertEqual(local_pool(self.instance, self.genome, seed),
                             reference_pool(self.instance, self.genome, seed, 16))

    def test_numeric_stage0_matches_traced_physics(self):
        for candidate in self.pool:
            fast = exact_stage0(self.instance, candidate.genome, self.params.arrays(self.instance))
            traced = stage0(self.instance, candidate.genome, self.params)
            full = decode(self.instance, candidate.genome, self.params)
            np.testing.assert_array_equal(fast.C, full.C[:self.instance.jobs])
            np.testing.assert_array_equal(fast.v, traced.v[:self.instance.jobs])
            np.testing.assert_allclose(fast.direct, [0., traced.energy, traced.labor], atol=1e-10)

    def test_scores_use_fixed_scales_and_reject_stale_parent(self):
        scales = self.parent.objectives * np.array([1.1, .8, .9])
        weights = np.array([1/3]*3)
        for method in ("cut_fatigue", "cut_time"):
            cache = build(self.instance, self.params, self.genome, self.parent, method, weights, scales, 0)
            observed, count, _ = scores(self.instance, self.params, self.genome, self.parent, self.pool, cache, 0)
            adjusted = weights * self.parent.objectives / scales
            cut = boundary_costates(self.instance, self.params, self.parent, adjusted, method == "cut_fatigue")
            expected = [cut_prediction(self.instance, self.parent, stage0(self.instance, c.genome, self.params), adjusted, cut)
                        for c in self.pool]
            np.testing.assert_allclose(observed, expected, atol=1e-14)
            self.assertEqual(count, 16)
            with self.assertRaisesRegex(AssertionError, "stale"):
                scores(self.instance, self.params, self.genome, self.parent, self.pool, cache, 1)

    def test_cache_and_fresh_paths_match_and_gain_telescopes(self):
        for method in ("cut_fatigue", "cut_time", "local_time"):
            args = (self.instance, self.params, self.genome, [1/3]*3, method, "steps", self.protocol, 839, 991)
            a, rows, epochs = run(*args)
            b, fresh, _ = run(*args, refresh_every_step=True)
            self.assertEqual(a["final_genome"], b["final_genome"])
            self.assertEqual([r["chosen_genome"] for r in rows], [r["chosen_genome"] for r in fresh])
            np.testing.assert_array_equal(a["final_objectives"], b["final_objectives"])
            self.assertEqual(a["full_decodes"], 7)
            self.assertEqual(sum(e["uses"] for e in epochs), 6)
            self.assertEqual(a["cache_builds"], 1 + sum(r["accepted"] for r in rows[:-1]))
            gain = sum(r["before_value"] - r["child_value"] for r in rows if r["accepted"])
            self.assertAlmostEqual(gain, a["gain"], places=12)

    def test_rejections_reuse_once_and_terminal_epoch_is_censored(self):
        summary, rows, epochs = run(self.instance, self.params, self.genome, [0., 0., 0.], "cut_fatigue",
                                    "steps", self.protocol, 839, 991)
        self.assertEqual(summary["accepted"], 0)
        self.assertEqual(summary["cache_builds"], 1)
        self.assertEqual(summary["actual_q"], 6)
        self.assertEqual(epochs[0]["closed_reason"], "terminal_right_censored")

    def test_late_improving_child_cannot_enter_deadline_result(self):
        clock, original = [0], []
        protocol = deepcopy(self.protocol)
        protocol["time_budget_seconds"] = 1e-6  # 1000 virtual ns

        def delayed(*args, **kwargs):
            result = decode(*args, **kwargs)
            if not original:
                original.append(result.objectives.copy())
                clock[0] += 100
                return result
            clock[0] += 10000
            return replace(result, objectives=original[0] * .9)

        with patch("research.fatigue_reuse.chain.perf_counter_ns", side_effect=lambda: clock[0]), \
             patch("research.fatigue_reuse.chain.decode", side_effect=delayed):
            summary, rows, _ = run(self.instance, self.params, self.genome, [1/3]*3, "random",
                                   "time", protocol, 839, 991)
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["would_improve"])
        self.assertFalse(rows[0]["on_time"])
        self.assertEqual(summary["gain"], 0.)
        self.assertEqual(summary["accepted"], 0)
        self.assertGreater(summary["overrun_ns"], 0)

    def test_offline_ledger_audit_reconstructs_actual_updates(self):
        summary, rows, epochs = run(self.instance, self.params, self.genome, [1/3]*3, "cut_fatigue",
                                    "steps", self.protocol, 839, 991)
        summary.update({"target": "balanced", "selector": "cut_fatigue"})
        check = audit_chain(self.instance, self.genome, summary, rows, epochs, self.protocol)
        self.assertEqual(check["rows_verified"], 6)

    def test_paired_bootstrap_preserves_instance_seed_units(self):
        data = []
        for instance in range(6):
            for seed in range(5):
                for method, gain in (("cut_fatigue", .2), ("cut_time", .1)):
                    data.append({"instance": instance, "parent_seed": seed, "method": method,
                                 "gain": gain, "elapsed_ns": 1000000000})
        result = paired(data, "cut_time", "gain")
        self.assertEqual(result["clusters"], 6)
        self.assertEqual(result["paired_parents"], 30)
        np.testing.assert_allclose(result["bootstrap_95_interval"], [.1, .1], atol=1e-14)


if __name__ == "__main__":
    unittest.main()
