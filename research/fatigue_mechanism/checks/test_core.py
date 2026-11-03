"""Small mathematical/physical checks; these do not measure optimizer quality."""
from dataclasses import replace
import json
import math
import unittest
import numpy as np

from ..model import FatigueParams, Genome, Instance
from ..decoder import decode, local_transition, local_transitions, replay
from ..adjoint import adjoint, adjoint_objectives
from ..validation import finite_difference_check, validate_schedule


def make_instance(rng, jobs=6, stages=2, factories=2):
    machines = tuple(tuple(rng.uniform(.7, 1.8, 3) for _ in range(stages)) for _ in range(factories))
    workers = tuple(tuple(rng.uniform(.7, 1.5, 2) for _ in range(stages)) for _ in range(factories))
    return Instance(rng.uniform(2., 10., (jobs, stages)), rng.uniform(.2, 2., (jobs, stages)),
                    machines, tuple(tuple(rng.uniform(3, 10, len(s)) for s in f) for f in machines),
                    tuple(tuple(rng.uniform(.2, 1, len(s)) for s in f) for f in machines), workers,
                    tuple(tuple(rng.uniform(5, 15, len(s)) for s in f) for f in workers),
                    "SYNTHETIC-UNIT-CHECK", "SYNTHETIC-independent-setup", "SYNTHETIC-standby")


def make_genome(rng, instance):
    js = tuple(map(int, rng.permutation(instance.jobs)))
    fa = [i % instance.factories for i in range(instance.jobs)]
    rng.shuffle(fa)
    return Genome(js, tuple(fa), tuple(int(rng.integers(len(instance.speeds[f][0]))) for f in fa),
                  tuple(int(rng.integers(len(instance.efficiencies[f][0]))) for f in fa))


def noncritical_case():
    instance = Instance(np.array([[4.], [10.], [8.]]), np.zeros((3, 1)),
                        (((1., 1.),),), (((3., 4.),),), (((1., 1.),),),
                        (((1., 1.),),), (((5., 6.),),), "SYNTHETIC-A-X-B", "ZERO-SETUP", "EXPLICIT-ONE")
    params = FatigueParams(.1, .1, .5)
    genome = Genome((0, 1, 2), (0, 0, 0), (0, 1, 1), (0, 1, 0))
    return instance, genome, params


class CoreChecks(unittest.TestCase):
    def test_noncritical_fatigue_channel(self):
        instance, genome, params = noncritical_case()
        result = decode(instance, genome, params)
        reverse = adjoint(result, instance, params)
        expected_c = 10 + 8 * (1 + .5 * (1 - math.exp(-.4)) * math.exp(-.6))
        expected_g = 8 * .5 * math.exp(-.6) * (.1 * math.exp(-.4) + .1 * (1 - math.exp(-.4)))
        self.assertAlmostEqual(result.C[2], expected_c, places=12)
        self.assertAlmostEqual(reverse.grad_base[0], expected_g, places=12)
        self.assertAlmostEqual(expected_c, 18.7237287797, places=9)
        self.assertAlmostEqual(expected_g, .2195246544, places=9)
        self.assertEqual(adjoint(result, instance, params, include_fatigue=False).grad_base[0], 0.)
        validate_schedule(instance, params, result)

    def test_position_vectors_and_topological_identity(self):
        rng = np.random.default_rng(371)
        instance = make_instance(rng)
        genome = make_genome(rng, instance)
        attrs = genome.by_job()
        changed = Genome.from_job_attributes(tuple(reversed(genome.js)), attrs)
        self.assertEqual(changed.by_job(), attrs)
        result = decode(instance, changed, FatigueParams(.1, .1, .5))
        validate_schedule(instance, FatigueParams(.1, .1, .5), result)
        self.assertNotEqual(result.execution_order, tuple(range(instance.operations)))
        self.assertTrue(any(p > o.op_id for o in result.operations for p in o.parents))
        for op in result.operations:
            self.assertEqual(op.factory, attrs[op.job][0])

    def test_minimal_forward_and_local_transition(self):
        rng = np.random.default_rng(45)
        instance = make_instance(rng)
        genome = make_genome(rng, instance)
        params = FatigueParams(.12, .04, .8, .15)
        full, minimal = decode(instance, genome, params), decode(instance, genome, params, False)
        np.testing.assert_array_equal(full.objectives, minimal.objectives)
        np.testing.assert_array_equal(full.C, minimal.C)
        np.testing.assert_array_equal(full.v, minimal.v)
        self.assertFalse(minimal.operations)
        for op in full.operations[:instance.jobs]:
            local = local_transition(instance, params, op.op_id, op.machine_id, op.worker_id, op.parents, full)
            np.testing.assert_array_equal([local.C, local.v, local.energy, local.labor, local.b, local.d, local.u, local.S],
                                          [op.C, op.v, op.energy, op.labor, op.b, op.d, op.u, op.S])
        first = full.operations[genome.js[0]]
        other_factory = 1 - first.factory
        moved = local_transition(instance, params, first.op_id, 0, 0, (-1, -1, -1), full, factory_id=other_factory)
        expected_base = ((instance.processing[first.job, 0] / instance.speeds[other_factory][0][0]
                          + instance.setup[first.job, 0]) / instance.efficiencies[other_factory][0][0])
        self.assertAlmostEqual(moved.base, expected_base)
        with self.assertRaises(ValueError):
            op = full.operations[instance.jobs]
            local_transition(instance, params, op.op_id, op.machine_id, op.worker_id, op.parents, full)
        np.testing.assert_array_equal(replay(instance, params, full).objectives, full.objectives)

    def test_random_fd_full_decoder_and_replay(self):
        rng = np.random.default_rng(20261031)
        totals = {"cases": 40, "objective_directions": 4, "replay_compared": 0, "full_compared": 0,
                  "replay_branch_changes": 0, "full_branch_or_topology_changes": 0,
                  "replay_max_scaled_error": 0., "full_max_scaled_error": 0.}
        for case in range(40):
            instance = make_instance(rng, jobs=6, stages=2 + case % 2)
            genome = make_genome(rng, instance)
            count = instance.worker_count
            params = FatigueParams(rng.uniform(.01, .12, count), rng.uniform(.01, .15, count),
                                    rng.uniform(.1, .9, count), rng.uniform(0, .2, count))
            result = decode(instance, genome, params)
            validate_schedule(instance, params, result)
            for weights in ((1., 0., 0.), (0., .01, 0.), (0., 0., .01), (.3, .003, .003)):
                report = finite_difference_check(instance, genome, params, weights)
                for key, val in report.items():
                    totals[key] = max(totals[key], val) if key.endswith("error") else totals[key] + val
        self.assertGreater(totals["full_compared"], 1000)
        self.assertLess(totals["replay_max_scaled_error"], 1e-6)
        self.assertLess(totals["full_max_scaled_error"], 1e-6)
        print("FATIGUE_FD_EVIDENCE " + json.dumps(totals, sort_keys=True))

    def test_batched_local_transitions_match_individual_and_validate_once(self):
        rng = np.random.default_rng(76)
        instance = make_instance(rng)
        genome = make_genome(rng, instance)
        params = FatigueParams(.12, .04, .8, .15)
        trace = decode(instance, genome, params)
        requests = [(o.op_id, o.machine_id, o.worker_id, o.parents, None)
                    for o in trace.operations[:instance.jobs]]
        requests.append((genome.js[0], 0, 0, (-1, -1, -1), 1 - trace.operations[genome.js[0]].factory))
        individual = tuple(local_transition(instance, params, i, m, w, parents, trace, factory_id=f)
                           for i, m, w, parents, f in requests)

        class CountedParams:
            calls = 0

            def arrays(self, instance):
                self.calls += 1
                return params.arrays(instance)

        counted = CountedParams()
        self.assertEqual(local_transitions(instance, counted, requests, trace), individual)
        self.assertEqual(counted.calls, 1)

    def test_parameter_limits_and_normalization(self):
        rng = np.random.default_rng(9)
        instance = make_instance(rng)
        genome = make_genome(rng, instance)
        for params in (FatigueParams(.1, .1, 0.), FatigueParams(0., .1, .8), FatigueParams(.1, 0., .8),
                       FatigueParams(.1, .1, .8, .3), FatigueParams(0., 0., .8, .3)):
            result = decode(instance, genome, params)
            validate_schedule(instance, params, result)
            report = finite_difference_check(instance, genome, params, (.3, .3, .4), (10., 100., 100.))
            self.assertLess(report["replay_max_scaled_error"], 1e-6)
            self.assertLess(report["full_max_scaled_error"], 1e-6)
            three = adjoint_objectives(result, instance, params, (10., 100., 100.))
            combined = adjoint(result, instance, params, (.3, .3, .4), (10., 100., 100.))
            np.testing.assert_allclose(combined.grad_base, sum(w * r.grad_base for w, r in zip((.3, .3, .4), three)), atol=1e-12)

    def test_alias_roles_and_idle_direct_dependency(self):
        instance = Instance(np.array([[4.], [8.]]), np.zeros((2, 1)), (((1.,),),), (((3.,),),),
                            (((2.,),),), (((1.,),),), (((5.,),),), "SYNTHETIC-ALIAS", "ZERO", "TWO")
        params = FatigueParams(.1, .05, .5, .2)
        genome = Genome((0, 1), (0, 0), (0, 0), (0, 0))
        original = decode(instance, genome, params)
        self.assertEqual(original.operations[1].parents, (-1, 0, 0))
        self.assertEqual(original.operations[1].tie_roles, (1, 2))
        # Algebraic network check also aliases the job role onto the same parent.
        alias = replace(original.operations[1], parents=(0, 0, 0), active_branch=0, tie_roles=(0, 1, 2))
        result = replace(original, operations=(original.operations[0], alias))
        result = replay(instance, params, result)
        base = np.array([o.base for o in result.operations])
        gradient = adjoint(result, instance, params, (.2, .03, .04)).grad_base
        for i in range(2):
            up, down = base.copy(), base.copy()
            up[i] += 1e-5
            down[i] -= 1e-5
            fd = np.array([.2, .03, .04]) @ (replay(instance, params, result, up).objectives - replay(instance, params, result, down).objectives) / 2e-5
            self.assertAlmostEqual(fd, gradient[i], places=7)
        # X waits for worker used on another machine, creating an internal gap.
        instance, genome, params = noncritical_case()
        genome = Genome((0, 1, 2), (0, 0, 0), (0, 0, 1), (0, 1, 1))
        report = finite_difference_check(instance, genome, params, (0., 1., 0.))
        self.assertLess(report["full_max_scaled_error"], 1e-6)

    def test_max_tie_selected_one_sided_branch(self):
        instance, _, _ = noncritical_case()
        instance = replace(instance, processing=np.array([[4.], [4.], [1.]]))
        genome = Genome((0, 1, 2), (0, 0, 0), (0, 1, 0), (0, 1, 1))
        params = FatigueParams(0., 0., 0.)
        result = decode(instance, genome, params)
        self.assertEqual(result.operations[2].tie_roles, (1, 2))
        self.assertEqual(result.operations[2].active_branch, 1)
        # Increase selected machine predecessor: right derivative follows it.
        base = np.array([o.base for o in result.operations])
        up = base.copy(); up[0] += 1e-6
        right = (replay(instance, params, result, up).objectives[0] - result.objectives[0]) / 1e-6
        self.assertAlmostEqual(right, adjoint(result, instance, params).grad_base[0], places=7)
        report = finite_difference_check(instance, genome, params)
        self.assertGreater(report["replay_branch_changes"], 0)

    def test_negative_start_slope_is_flagged(self):
        instance, genome, _ = noncritical_case()
        params = FatigueParams(.1, 1., 100., .8)
        result = decode(instance, genome, params)
        self.assertTrue(any(o.negative_start_slope for o in result.operations))
        validate_schedule(instance, params, result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
