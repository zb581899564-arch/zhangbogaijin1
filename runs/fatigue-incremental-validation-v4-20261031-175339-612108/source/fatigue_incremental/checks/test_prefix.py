from copy import deepcopy
import unittest
import numpy as np
from research.fatigue_mechanism.checks.test_core import make_instance
from research.fatigue_mechanism.instances import parent_genome
from research.fatigue_mechanism.model import FatigueParams, Genome
from research.fatigue_mechanism.decoder import decode
from research.fatigue_reuse.stage0 import exact_stage0
from research.fatigue_reuse.neighbors import local_pool
from research.fatigue_reuse.chain import run
from ..prefix import build_prefix, incremental_stage0
from ..protocol import PROTOCOL
from .. import scorer


class PrefixChecks(unittest.TestCase):
    def setUp(self):
        self.instance = make_instance(np.random.default_rng(13931), jobs=20, stages=3)
        self.genome = parent_genome(self.instance, 23)
        self.params = FatigueParams(.1, .08, .7, .2)
        self.parent = decode(self.instance, self.genome, self.params)
        self.cache = build_prefix(self.instance, self.genome, self.parent)
        self.arrays = self.params.arrays(self.instance)

    def compare(self, genome, cache=None, arrays=None):
        incremental, work = incremental_stage0(self.instance, genome, arrays or self.arrays, cache or self.cache)
        full = exact_stage0(self.instance, genome, arrays or self.arrays)
        for name in ("C", "v", "direct"):
            np.testing.assert_array_equal(getattr(incremental, name), getattr(full, name))
        self.assertEqual(work["recomputed_ops"] + work["reused_prefix_ops"] + work["unchanged_factory_ops"], self.instance.jobs)
        return work

    def test_all_local_kinds_exact_and_cache_immutable(self):
        before = self.cache.C.copy()
        for candidate in local_pool(self.instance, self.genome, 997):
            self.compare(candidate.genome)
        np.testing.assert_array_equal(before, self.cache.C)
        with self.assertRaises(ValueError):
            self.cache.C[0] = 0.

    def test_first_and_last_edits_reuse_exact_prefix(self):
        tokens = self.cache.factories[0].tokens
        for position in (0, len(tokens)-1):
            attrs = self.genome.by_job()
            j, m, w = tokens[position]
            attrs[j] = (0, (m+1) % 3, w)
            child = Genome.from_job_attributes(self.genome.js, attrs)
            work = self.compare(child)
            self.assertEqual(work["reused_prefix_ops"], position)
            self.assertEqual(work["recomputed_ops"], len(tokens)-position)

    def test_global_interleaving_change_needs_no_physics(self):
        attrs = self.genome.by_job()
        js = [j for factory in self.cache.factories for j, _, _ in factory.tokens]
        work = self.compare(Genome.from_job_attributes(js, attrs))
        self.assertEqual(work["recomputed_ops"], 0)
        self.assertEqual(work["unchanged_factory_ops"], self.instance.jobs)

    def test_multiple_affected_factories_and_FA_rejection(self):
        attrs = self.genome.by_job()
        jobs = []
        for f, factory in enumerate(self.cache.factories):
            j, m, w = factory.tokens[-1]
            attrs[j] = (f, (m+1) % 3, w)
            jobs.append(j)
        work = self.compare(Genome.from_job_attributes(self.genome.js, attrs))
        self.assertEqual(work["affected_factory_visits"], 2)
        attrs[jobs[0]], attrs[jobs[1]] = attrs[jobs[1]], attrs[jobs[0]]
        with self.assertRaisesRegex(ValueError, "fixed per-job factory"):
            self.compare(Genome.from_job_attributes(self.genome.js, attrs))

    def test_parameter_limits_and_initial_fatigue(self):
        for params in (FatigueParams(0, .1, .7, .3), FatigueParams(.1, 0, .7, .3), FatigueParams(.1, .1, 0, .3)):
            parent = decode(self.instance, self.genome, params)
            cache = build_prefix(self.instance, self.genome, parent)
            for candidate in local_pool(self.instance, self.genome, 997)[:4]:
                self.compare(candidate.genome, cache, params.arrays(self.instance))

    def test_fixed_budget_incremental_and_full_trajectories_match(self):
        protocol = deepcopy(PROTOCOL)
        protocol["decisions"] = 8
        for method in ("cut_fatigue", "cut_time"):
            args = (self.instance, self.params, self.genome, [1/3]*3, method, "steps", protocol, 997, 313)
            incremental, rows, epochs = run(*args, score_engine=scorer)
            full, reference_rows, _ = run(*args)
            self.assertEqual(incremental["final_genome"], full["final_genome"])
            for a, b in zip(rows, reference_rows):
                self.assertEqual(a["chosen_genome"], b["chosen_genome"])
                np.testing.assert_array_equal(a["scores"], b["scores"])
            for epoch in epochs:
                work = epoch["incremental_work"]
                self.assertEqual(work["equivalent_full_ops"], work["recomputed_ops"] + work["reused_prefix_ops"] + work["unchanged_factory_ops"])


if __name__ == "__main__":
    unittest.main()
