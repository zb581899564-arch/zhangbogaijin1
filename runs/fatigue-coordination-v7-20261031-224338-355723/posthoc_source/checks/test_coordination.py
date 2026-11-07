"""Targeted checks; no optimization or experiment outcome tuning."""
import os
for name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[name] = "1"

from dataclasses import replace
from fractions import Fraction
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from scipy.sparse import csr_matrix
from research.fatigue_mechanism.decoder import decode, _validate_genome
from research.fatigue_mechanism.validation import validate_schedule
from ..analysis import minima, plateaus, analyze, best_path
from ..controls import run_trial, exact_probability
from ..instances import make_instance, parameters
from ..space import Space, build_graph, moves


class CoordinationChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = build_graph(Space(3))
        cls.instance = make_instance(3, 17417)
        cls.params, _ = parameters(cls.instance, 17417)

    def test_physical_space_and_single_job_invariants(self):
        graph = self.graph
        self.assertEqual(graph.space.size, 768)
        self.assertEqual(Space(4).size, 18432)
        self.assertEqual(len(graph.destination), 25344)
        self.assertEqual(len({graph.space.state(i).genome() for i in range(768)}), 768)
        matrix = csr_matrix((np.ones(len(graph.destination)), (graph.source, graph.destination)), shape=(768, 768))
        self.assertEqual((matrix != matrix.T).nnz, 0)
        for index in (0, 17, 203, 767):
            state = graph.space.state(index)
            _validate_genome(self.instance, state.genome())
            for job in range(3):
                for child in moves(state, job):
                    _validate_genome(self.instance, child.genome())
                    self.assertIn(state, moves(child, job))
                    for other in set(range(3))-{job}:
                        self.assertEqual(state.genome().by_job()[other], child.genome().by_job()[other])
                    self.assertEqual(tuple(tuple(j for j in q if j != job) for q in state.queues),
                                     tuple(tuple(j for j in q if j != job) for q in child.queues))

    def test_two_step_minima_against_explicit_paths(self):
        graph = self.graph
        values = np.random.default_rng(173).normal(size=768)
        by_job, one, two = minima(graph, values)
        result = analyze(graph, values, 1e-10)
        for state in (0, 1, 7, 93, 351, 767):
            endpoints = [int(end) for first in range(3) for mid in graph.neighbors(state, first)
                         for second in range(3) if first != second for end in graph.neighbors(mid, second)]
            self.assertEqual(two[state], min(values[endpoints]))
            first, mid, second, end = best_path(graph, values, result, state)
            self.assertNotEqual(first, second)
            self.assertEqual(values[end], two[state])
            self.assertEqual(one[state], min(by_job[state]))

    def test_neutral_escape_is_not_uphill_barrier(self):
        graph = SimpleNamespace(source=np.array([0, 1, 1, 2]), destination=np.array([1, 0, 2, 1]))
        flat = plateaus(graph, np.array([1., 1., 0.]), np.array([1., 0., 1.]), np.array([0., 1., 0.]), 1e-10)
        self.assertTrue(flat["weak"][0])
        self.assertFalse(flat["strict"][0])
        uphill = plateaus(graph, np.array([1., 2., 0.]), np.array([2., 0., 2.]), np.array([0., 2., 0.]), 1e-10)
        self.assertTrue(uphill["strict"][0])
        drift = plateaus(graph, np.array([1., 1.+.75e-10, 1.+1.5e-10]),
                         np.ones(3), np.zeros(3), 1e-10)
        self.assertFalse(drift["component_certified"].any())
        self.assertFalse(drift["strict"].any())

    def test_same_decoder_beta_zero_rate_invariance_and_trace(self):
        instance, params = self.instance, self.params
        self.assertTrue(all(len(instance.efficiencies[f][1]) < len(instance.speeds[f][1]) for f in range(2)))
        for index in (0, 93, 767):
            genome = self.graph.space.state(index).genome()
            baseline = decode(instance, genome, params["beta0"])
            changed = decode(instance, genome, replace(params["beta0"], alpha=12., mu=3.))
            np.testing.assert_array_equal(baseline.objectives, changed.objectives)
            np.testing.assert_array_equal(baseline.C, changed.C)
            for name, p in params.items():
                full, minimal = decode(instance, genome, p), decode(instance, genome, p, retain_trace=False)
                np.testing.assert_array_equal(full.objectives, minimal.objectives)
                np.testing.assert_array_equal(full.C, minimal.C)
                np.testing.assert_array_equal(full.v, minimal.v)
                validate_schedule(instance, p, full)
        other = make_instance(4, 17417)
        self.assertFalse(np.array_equal(instance.speeds[0][0], other.speeds[0][0]))

    def test_live_controls_pay_all_decodes(self):
        state = self.graph.space.state(193)
        reference = decode(self.instance, state.genome(), self.params["beta0"]).objectives
        for method in ("single_job", "plain_composite", "machine_pair", "worker_pair"):
            with patch("research.fatigue_coordination.controls.decode", wraps=decode) as counted:
                trial = run_trial(self.instance, self.params["strong_slow"], state, [0, 1, 0], reference, method, 29, 16)
            self.assertEqual(counted.call_count, 17)
            self.assertEqual(trial["rng_seed"], 29)
            self.assertNotIn("seed", trial)
            self.assertEqual(trial["full_decodes"], 17)
            self.assertEqual(len(trial["rows"]), 16)
            self.assertGreater(trial["elapsed_ns"], 0)
            self.assertEqual(trial["best_value"], min([trial["before_value"]]+[r["value"] for r in trial["rows"]]))

    def test_probability_respects_labelled_path_weights(self):
        graph = self.graph
        values = np.random.default_rng(91).normal(size=768)
        pairs = ((0, 1), (2, 0))
        state = 77
        total = Fraction(0)
        for first, second in pairs:
            middles = graph.neighbors(state, first)
            for mid in middles:
                ends = graph.neighbors(mid, second)
                success = sum(values[end] < values[state]-1e-10 for end in ends)
                total += Fraction(success, len(pairs)*len(middles)*len(ends))
        result = exact_probability(graph, values, state, "plain_composite", pairs, 1e-10, 16)
        self.assertAlmostEqual(result["one_draw_success"], float(total), places=14)
        self.assertAlmostEqual(result["budget_success"], 1-(1-float(total))**16, places=14)
        self.assertTrue(result["noop_endpoint_in_pool"])


if __name__ == "__main__":
    unittest.main()
