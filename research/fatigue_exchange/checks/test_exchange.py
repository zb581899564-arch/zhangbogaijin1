"""Legality, shared-pool information controls, FE and real deadline semantics."""
import os
for name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[name] = "1"
from collections import Counter
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from research.fatigue_mechanism.decoder import decode, _validate_genome
from research.fatigue_reuse.stage0 import exact_stage0
from research.fatigue_coordination.instances import make_instance, parameters
from research.fatigue_coordination.space import Space, build_graph
from ..operators import exchange, labelled_children, pool, resource
from ..coverage import n2_endpoints, row
from ..chain import run
from .. import scoring


class ExchangeChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.instance = make_instance(3, 17417)
        cls.params, _ = parameters(cls.instance, 17417)
        cls.graph = build_graph(Space(3))
        cls.state = cls.graph.space.state(137)

    def test_exchange_preserves_slots_job_resources_and_nonempty_factories(self):
        for n in (3, 4):
            space = Space(n)
            instance = make_instance(n, 17417)
            for index in (0, 137, space.size-1):
                state = space.state(index)
                for kind in ("swap", "swap_rebind", "rebind"):
                    for child in labelled_children(state, kind):
                        _validate_genome(instance, child.genome())
                        self.assertEqual(tuple(map(len, child.queues)), tuple(map(len, state.queues)))
                        if kind == "swap":
                            self.assertEqual(child.resources, state.resources)
                        if kind == "rebind":
                            self.assertEqual(child.queues, state.queues)
                            self.assertNotEqual(child.resources, state.resources)
                a, b = state.queues[0][0], state.queues[1][0]
                self.assertEqual(exchange(exchange(state, a, b), a, b), state)
                self.assertEqual(resource(exchange(state, a, b), a), resource(state, a))

    def test_coverage_matches_physical_dedup_and_label_weights(self):
        graph, parent = self.graph, 137
        n2 = n2_endpoints(graph, parent)
        values = np.random.default_rng(541).random(768)
        for kind in ("swap", "swap_rebind", "rebind"):
            ids = np.array([graph.space.index(c) for c in labelled_children(self.state, kind)])
            result = row(values, parent, ids, n2, int(np.sum(values[n2] < values[parent]-1e-10)), 1e-10)
            histogram = Counter(map(int, ids))
            expected = sum(count for i, count in histogram.items() if values[i] < values[parent]-1e-10)/len(ids)
            self.assertAlmostEqual(result["one_draw_success"], expected)
            self.assertEqual(result["unique_endpoints"], len(histogram))
            self.assertTrue(0 <= result["improving_N2_coverage"] <= 1)
            if kind != "rebind":
                self.assertEqual(result["outside_N2_endpoints"], 0)
        singleton = graph.space.state(0)
        rebind = {graph.space.index(c) for c in labelled_children(singleton, "rebind")}
        self.assertTrue(rebind-set(map(int, n2_endpoints(graph, 0))))

    def test_exact_stage0_matches_full_migrating_candidates(self):
        candidates = pool(self.state, "swap_rebind", 21871, 8)
        self.assertEqual(candidates, pool(self.state, "swap_rebind", 21871, 8))
        for p in self.params.values():
            for candidate in candidates:
                full = decode(self.instance, candidate.genome, p)
                first = exact_stage0(self.instance, candidate.genome, p.arrays(self.instance))
                np.testing.assert_array_equal(first.C, full.C[:3])
                np.testing.assert_array_equal(first.v, full.v[:3])

    def test_beta0_information_control_has_identical_scores_and_trajectories(self):
        p, state = self.params["beta0"], self.state
        parent = decode(self.instance, state.genome(), p)
        candidates = pool(state, "swap_rebind", 7321, 8)
        scores = []
        for method in ("pool_time", "pool_fatigue"):
            cache = scoring.build(self.instance, p, state, parent, method, parent.objectives, 0)
            scores.append(scoring.scores(self.instance, p, state, parent, candidates, cache, method, 0)[0])
            with self.assertRaises(AssertionError):
                scoring.scores(self.instance, p, state, parent, candidates, cache, method, 1)
        np.testing.assert_array_equal(*scores)
        a = run(self.instance, p, state, "pool_time", 92821, "FE")
        b = run(self.instance, p, state, "pool_fatigue", 92821, "FE")
        self.assertEqual(a["final_state"], b["final_state"])
        self.assertEqual([r["chosen"] for r in a["steps"]], [r["chosen"] for r in b["steps"]])

    def test_full_FE_and_partial_reconstructions_are_separate(self):
        for method in ("plain", "rebind", "swap", "swap_rebind", "pool_random", "pool_cheap", "pool_time", "pool_fatigue"):
            with patch("research.fatigue_exchange.chain.decode", wraps=decode) as counted:
                result = run(self.instance, self.params["strong_fast"], self.state, method, 92821, "FE")
            self.assertEqual(counted.call_count, 33)
            self.assertEqual(result["full_decodes"], 33)
            self.assertEqual(result["partial_calls"], 256 if method in ("pool_time", "pool_fatigue") else 0)
            self.assertGreaterEqual(result["bookkeeping_ns"], 0)

    def test_late_improving_child_is_charged_but_never_returned(self):
        parent = decode(self.instance, self.state.genome(), self.params["beta0"])
        fake = SimpleNamespace(objectives=parent.objectives*.5)
        record = {"improves": True, "partial_calls": 0, "stage0_ns": 0}
        ticks = iter((0, 0, 2_000_000_000, 3_000_000_000, 4_000_000_000))
        with patch("research.fatigue_exchange.chain.decide", return_value=(record, self.state, fake, None)):
            result = run(self.instance, self.params["beta0"], self.state, "swap", 1, "time", 1., clock=lambda: next(ticks))
        self.assertEqual(result["full_decodes"], 2)
        self.assertEqual(result["accepted"], 0)
        self.assertEqual(result["gain"], 0.)
        self.assertFalse(result["steps"][0]["on_time"])


if __name__ == "__main__":
    unittest.main()
