"""Checks of selector isolation and the shared legal pool, not optimizer tests."""
from dataclasses import replace
import unittest
from unittest.mock import patch
import numpy as np
from .test_core import make_instance
from ..adjoint import adjoint
from ..candidates import Candidate, candidate_pool
from ..decoder import decode, _transition
from ..instances import parent_genome
from ..model import FatigueParams
from ..prediction import prepare_defects, score_defects
from ..statistics import select_minima, selection_metrics
from ..validation import validate_schedule


class PredictionChecks(unittest.TestCase):
    def setUp(self):
        self.instance = make_instance(np.random.default_rng(991), jobs=20)
        self.parent = parent_genome(self.instance, 7)
        self.params = FatigueParams(.1, .03, .7)
        self.pool = candidate_pool(self.instance, self.parent, 911)
        self.trace = decode(self.instance, self.parent, self.params)

    def test_common_legal_pool_and_job_owned_resources(self):
        self.assertEqual(self.pool, candidate_pool(self.instance, self.parent, 911))
        self.assertEqual(len({c.genome for c in self.pool}), 16)
        attrs = self.parent.by_job()
        for candidate in self.pool:
            for job, row in candidate.genome.by_job().items():
                self.assertEqual(row[0], attrs[job][0])
            if candidate.kind in ("order_swap", "order_insert"):
                self.assertEqual(candidate.genome.by_job(), attrs)
            validate_schedule(self.instance, self.params, decode(self.instance, candidate.genome, self.params))

    def test_no_oracle_access_and_unchanged_zero(self):
        reverse = adjoint(self.trace, self.instance, self.params, (1, 1, 1), self.trace.objectives)
        poisoned = replace(self.trace, objectives=np.full(3, np.nan))
        with patch("research.fatigue_mechanism.decoder.decode", side_effect=AssertionError("oracle accessed")):
            normal = prepare_defects(self.instance, self.params, self.trace, self.pool)
            isolated = prepare_defects(self.instance, self.params, poisoned, self.pool)
            np.testing.assert_array_equal(score_defects(normal, reverse), score_defects(isolated, reverse))
            unchanged = prepare_defects(self.instance, self.params, self.trace, [Candidate("identity", (0, 1), self.parent)])
            self.assertEqual(score_defects(unchanged, reverse)[0], 0.)

    def test_beta_zero_full_and_time_control_agree(self):
        params = FatigueParams(.1, .03, 0.)
        trace = decode(self.instance, self.parent, params)
        defects = prepare_defects(self.instance, params, trace, self.pool)
        for weights in ((1, 0, 0), (0, 1, 0), (0, 0, 1), (1/3, 1/3, 1/3)):
            full = adjoint(trace, self.instance, params, weights, trace.objectives)
            control = adjoint(trace, self.instance, params, weights, trace.objectives, False)
            np.testing.assert_allclose(score_defects(defects, full), score_defects(defects, control), atol=1e-14)

    def test_defect_score_is_frozen_graph_residual_directional_derivative(self):
        """Independently inject residuals; this does NOT assert discrete accuracy."""
        defects = prepare_defects(self.instance, self.params, self.trace, self.pool)
        arrays = self.params.arrays(self.instance)

        def forced_objectives(defect, theta):
            C, H = np.zeros(self.instance.operations), np.zeros(self.instance.operations)
            injected = {op_id: index for index, op_id in enumerate(defect.ids)}
            energy = labor = 0.
            for op_id in self.trace.execution_order:
                old = self.trace.operations[op_id]
                values, _ = _transition(self.instance, arrays, op_id, old.factory, old.machine_id,
                                        old.worker_id, old.parents, C, H)
                C[op_id], H[op_id] = values[:2]
                energy += values[2]
                labor += values[3]
                if op_id in injected:
                    index = injected[op_id]
                    C[op_id] += theta * defect.state_change[index, 0]
                    H[op_id] += theta * defect.state_change[index, 1]
                    energy += theta * defect.direct_change[index, 1]
                    labor += theta * defect.direct_change[index, 2]
            return np.array([max(C[list(self.trace.final_ops)]), energy, labor])

        directions = ((1, 0, 0), (0, 1, 0), (0, 0, 1), (1/3, 1/3, 1/3))
        fd_vectors = np.array([(forced_objectives(d, 1e-7) - forced_objectives(d, -1e-7)) / 2e-7 for d in defects])
        for weights in directions:
            full = adjoint(self.trace, self.instance, self.params, weights, self.trace.objectives)
            expected = fd_vectors @ (np.asarray(weights) / self.trace.objectives)
            np.testing.assert_allclose(score_defects(defects, full), expected, atol=1e-7, rtol=1e-7)

    def test_uniform_ties_and_random_do_not_cherry_pick(self):
        actual = np.array([-.1, .2, -.3])
        fixed = select_minima([0, 0, 0]).tolist()
        for scores in (np.zeros(3), None):
            result = selection_metrics(scores, actual)
            self.assertEqual(result["tie_indices"], fixed)
            self.assertAlmostEqual(result["accepted_gain"], .4/3)
            self.assertAlmostEqual(result["selected_raw_gain"], .2/3)
            self.assertAlmostEqual(result["improvement_probability"], 2/3)


if __name__ == "__main__":
    unittest.main()
