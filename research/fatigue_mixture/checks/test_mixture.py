"""Check policy mechanics independently of experimental performance."""
import os
for name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[name] = "1"
from collections import Counter
from dataclasses import asdict
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from research.fatigue_mechanism.decoder import decode, _validate_genome
from research.fatigue_coordination.instances import make_instance, parameters
from research.fatigue_coordination.space import Space, build_graph
from research.fatigue_exchange.operators import pool, labelled_children
from research.fatigue_exchange.coverage import n2_endpoints
from ..policy import family, candidate
from ..coverage import probabilities
from ..chain import run


class MixtureChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = build_graph(Space(4))
        cls.instance = make_instance(4, 271003)
        cls.params, _ = parameters(cls.instance, 271003)
        cls.state = cls.graph.space.state(6826)

    def test_alternation_exact_quota_and_independent_proposal_stream(self):
        seeds = {"branch": 91, "proposal": 193}
        for seed in (1, 7, 17, 193, 743777):
            labels = [family("mix_alternate", i, seed) for i in range(32)]
            self.assertEqual(Counter(labels), {"plain": 16, "swap_rebind": 16})
            self.assertTrue(all(a != b for a, b in zip(labels, labels[1:])))
        for method in ("mix_iid", "mix_alternate"):
            for step in range(32):
                label, actual_seed, state = candidate(self.state, method, step, seeds)
                changed = candidate(self.state, method, step, {**seeds, "proposal": 271})
                self.assertEqual(label, changed[0])
                self.assertEqual(state, pool(self.state, label, actual_seed, 1)[0].state)
                _validate_genome(self.instance, state.genome())
        self.assertEqual(self.state, self.graph.space.state(6826))

    def test_mixture_retains_plain_support_not_new_endpoints(self):
        for parent in (0, 137, 6826, 18431):
            n2 = set(map(int, n2_endpoints(self.graph, parent)))
            swaps = {self.graph.space.index(c) for c in labelled_children(self.graph.space.state(parent), "swap_rebind")}
            self.assertTrue(swaps <= n2)
            self.assertEqual(n2 | swaps, n2)

    def test_probability_formulas_and_fixed_parent_balancing(self):
        a, b = .1, .4
        self.assertAlmostEqual(probabilities(a, b, "mix_iid", 16), 1-.75**16)
        self.assertAlmostEqual(probabilities(a, b, "mix_alternate", 16), 1-.9**8*.6**8)
        self.assertGreaterEqual(probabilities(a, b, "mix_alternate", 32), probabilities(a, b, "mix_iid", 32))
        self.assertEqual(probabilities(0., 0., "mix_iid", 32), 0.)
        self.assertEqual(probabilities(0., 1., "mix_alternate", 32), 1.)

    def test_all_methods_pay_exactly33_full_evaluations_and_no_partial(self):
        for method in ("plain", "swap_rebind", "mix_iid", "mix_alternate"):
            with patch("research.fatigue_mixture.chain.decode", wraps=decode) as counted:
                result = run(self.instance, self.params["strong_fast"], self.state, method, 743777, "FE")
            self.assertEqual(counted.call_count, 33)
            self.assertEqual(result["full_decodes"], 33)
            self.assertEqual(result["partial_calls"], 0)
            if method == "mix_alternate":
                self.assertEqual(Counter(r["family"] for r in result["steps"]), {"plain": 16, "swap_rebind": 16})

    def test_fixed_seed_replay_and_beta0_changes_no_policy_branch(self):
        values = [run(self.instance, self.params[m], self.state, "mix_iid", 743777, "FE")
                  for m in ("beta0", "beta0", "strong_fast")]
        self.assertEqual(values[0]["final_state"], values[1]["final_state"])
        self.assertEqual([s["child_state"] for s in values[0]["steps"]], [s["child_state"] for s in values[1]["steps"]])
        self.assertEqual([s["family"] for s in values[0]["steps"]], [s["family"] for s in values[2]["steps"]])

    def test_late_improvement_is_charged_and_excluded(self):
        parent = decode(self.instance, self.state.genome(), self.params["beta0"])
        child = SimpleNamespace(objectives=parent.objectives*.5)
        row = {"family": "plain", "improves": True, "partial_calls": 0}
        ticks = iter((0, 0, 2_000_000_000, 3_000_000_000, 4_000_000_000))
        with patch("research.fatigue_mixture.chain.decision", return_value=(row, self.state, child)):
            result = run(self.instance, self.params["beta0"], self.state, "mix_iid", 1, "time", 1., clock=lambda: next(ticks))
        self.assertEqual(result["full_decodes"], 2)
        self.assertEqual(result["gain"], 0.)
        self.assertEqual(result["final_state"], asdict(self.state))
        self.assertFalse(result["steps"][0]["on_time"])


if __name__ == "__main__":
    unittest.main()
