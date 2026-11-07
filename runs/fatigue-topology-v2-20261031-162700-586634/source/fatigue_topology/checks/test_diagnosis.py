import unittest
import json
from copy import deepcopy
from unittest.mock import patch
import numpy as np
from research.fatigue_mechanism.checks.test_core import make_instance
from research.fatigue_mechanism.instances import parent_genome
from research.fatigue_mechanism.model import FatigueParams
from research.fatigue_mechanism.decoder import decode, replay
from research.fatigue_mechanism.validation import validate_schedule
from ..protocol import PROTOCOL
from ..trials import make_pool, trial_instance
from ..counterfactual import stage0, fixed_later, boundary_costates, cut_prediction
from ..scoring import prepare, reverses, predictions
from ..diagnostics import regime
from ..case import run_pool
from ..timing import Accounting, case_timing


class DiagnosisChecks(unittest.TestCase):
    def setUp(self):
        self.instance = make_instance(np.random.default_rng(83771), jobs=20, stages=3)
        self.genome = parent_genome(self.instance, 11)
        self.params = FatigueParams(.1, .08, .7)
        self.trace = decode(self.instance, self.genome, self.params)

    def test_identity_fixed_later_and_boundary(self):
        first = stage0(self.instance, self.genome, self.params)
        frozen = fixed_later(self.instance, self.params, first, self.trace)
        np.testing.assert_allclose(frozen.C, self.trace.C, atol=1e-12)
        np.testing.assert_allclose(frozen.v, self.trace.v, atol=1e-12)
        np.testing.assert_allclose(frozen.objectives, self.trace.objectives, atol=1e-10)
        validate_schedule(self.instance, self.params, frozen)
        self.assertEqual(regime(self.trace, frozen, self.instance.jobs)["full_regime"], "graph_same_branch_same")
        for weights in PROTOCOL["targets"].values():
            cut = boundary_costates(self.instance, self.params, self.trace, weights)
            self.assertAlmostEqual(cut_prediction(self.instance, self.trace, first, weights, cut), 0., places=14)

    def test_new_stage0_and_frozen_routes_are_feasible(self):
        for name in ("legal_local", "legal_broad"):
            for trial in make_pool(self.instance, self.genome, 83, name, PROTOCOL):
                first = stage0(self.instance, trial.genome, self.params)
                full = decode(self.instance, trial.genome, self.params)
                frozen = fixed_later(self.instance, self.params, first, self.trace)
                np.testing.assert_array_equal(first.C[:self.instance.jobs], full.C[:self.instance.jobs])
                validate_schedule(self.instance, self.params, frozen)
                validate_schedule(self.instance, self.params, full)

    def test_probe_fixed_later_matches_independent_old_replay(self):
        for trial in make_pool(self.instance, self.genome, 83, "probe_0.01", PROTOCOL):
            changed = trial_instance(self.instance, trial)
            first = stage0(changed, trial.genome, self.params)
            frozen = fixed_later(changed, self.params, first, self.trace)
            old_replay = replay(changed, self.params, self.trace)
            np.testing.assert_allclose(frozen.objectives, old_replay.objectives, atol=1e-10)
            np.testing.assert_array_equal(frozen.C, old_replay.C)

    def test_cut_linear_matches_frozen_response_for_tiny_probe(self):
        for trial in make_pool(self.instance, self.genome, 83, "probe_1e-05", PROTOCOL):
            changed = trial_instance(self.instance, trial)
            first = stage0(changed, trial.genome, self.params)
            frozen = fixed_later(changed, self.params, first, self.trace)
            for weights in PROTOCOL["targets"].values():
                cut = boundary_costates(self.instance, self.params, self.trace, weights)
                predicted = cut_prediction(self.instance, self.trace, first, weights, cut)
                actual = (frozen.objectives - self.trace.objectives) @ (np.asarray(weights) / self.trace.objectives)
                self.assertLess(abs(predicted - actual), 1e-9)

    def test_generation_is_legal_and_prediction_does_not_decode(self):
        reverse = reverses(self.instance, self.params, self.trace, PROTOCOL["targets"])
        for name in PROTOCOL["pools"]:
            pool = make_pool(self.instance, self.genome, 83, name, PROTOCOL)
            self.assertEqual(pool, make_pool(self.instance, self.genome, 83, name, PROTOCOL))
            for trial in pool:
                if trial.relative_st:
                    changed = trial_instance(self.instance, trial)
                    self.assertTrue(np.all(changed.processing > 0))
                self.assertEqual({j: a[0] for j, a in trial.genome.by_job().items()},
                                 {j: a[0] for j, a in self.genome.by_job().items()})
            with patch("research.fatigue_mechanism.decoder.decode", side_effect=AssertionError("truth leaked")):
                defects = prepare(self.instance, self.params, self.trace, pool)
                result = predictions(self.instance, self.trace, pool, defects, reverse)
                self.assertEqual(set(result), set(PROTOCOL["targets"]))

    def test_one_synthetic_pool_end_to_end_serializes(self):
        protocol = deepcopy(PROTOCOL)
        protocol["targets"] = {"balanced": [1/3, 1/3, 1/3]}
        protocol["timing_repeats"] = 1
        counter, emitted = Accounting(), []
        reverse = reverses(self.instance, self.params, self.trace, protocol["targets"])
        common = case_timing(counter, self.instance, self.params, self.genome, self.trace, protocol["targets"], 1)
        factory = lambda: make_pool(self.instance, self.genome, 83, "probe_0.01", protocol)
        obs, selected = run_pool(counter, self.instance, self.params, self.trace, factory(), factory, reverse,
                                  {"pool": "probe_0.01"}, protocol, common, lambda name, value: emitted.append((name, value)))
        json.dumps(emitted, allow_nan=False)
        self.assertEqual(len(obs), 8)
        self.assertEqual(len(selected), 3)
        self.assertEqual(counter.calls["offline_adaptive_truth"], 8)


if __name__ == "__main__":
    unittest.main()
