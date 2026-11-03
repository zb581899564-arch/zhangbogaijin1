"""Independent enumeration verifies the extension, not its performance."""
import os
for name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[name] = "1"
from collections import Counter
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from research.fatigue_coordination.space import Space, moves
from research.fatigue_coordination.instances import make_instance, parameters
from research.fatigue_exchange.operators import labelled_children
from research.fatigue_mechanism.decoder import decode, _validate_genome
from ..state import State, insert, replay
from ..operators import segments, indexed_move, one_move, cross_pair, draw
from ..chain import run


def brute(state, job, dims):
    source = next(f for f, q in enumerate(state.queues) if job in q)
    result = set()
    for target, (machines, workers) in enumerate(dims):
        if target != source and len(state.queues[source]) == 1:
            continue
        length = len(state.queues[target])-(target == source)
        for position in range(length+1):
            for m in range(machines):
                for w in range(workers):
                    candidate = insert(state, job, target, position, m, w)
                    if candidate != state:
                        result.add(candidate)
    return result


class ScaleChecks(unittest.TestCase):
    def test_v9_complete_N1_support_bridge(self):
        space = Space(3)
        for index in (0, 17, 137, 351, 767):
            old = space.state(index)
            state = State.from_genome(old.genome(), 2)
            for job in range(3):
                _, parts = segments(state, job, ((2, 2), (2, 2)))
                actual = [indexed_move(state, job, ((2, 2), (2, 2)), rank)[0] for rank in range(sum(p[1] for p in parts))]
                expected = {State.from_genome(c.genome(), 2) for c in moves(old, job)}
                self.assertEqual(len(actual), len(set(actual)))
                self.assertEqual(set(actual), expected)

    def test_heterogeneous_rank_and_immovable_singleton(self):
        state = State(((0,), (1, 2), (3,)), ((0, 0),)*4)
        dims = ((1, 1), (2, 1), (3, 2))
        for job in range(4):
            _, parts = segments(state, job, dims)
            actual = {indexed_move(state, job, dims, rank)[0] for rank in range(sum(p[1] for p in parts))}
            self.assertEqual(actual, brute(state, job, dims))
        self.assertEqual(one_move(state, 0, dims, np.random.default_rng(1)), (state, None))

    def test_cross_pairs_uniform_rank_mapping_and_replay(self):
        state = State(((0,), (1, 2), (3,)), ((0, 0),)*4)
        class Ranked:
            def __init__(self, rank): self.rank = rank
            def integers(self, size): return self.rank
        pairs = [cross_pair(state, Ranked(i))[2:] for i in range(5)]
        self.assertEqual(len(set(pairs)), 5)
        dims = ((1, 1), (2, 1), (3, 2))
        for family in ("plain", "swap_rebind"):
            for seed in range(32):
                child, edit = draw(state, family, dims, seed)
                self.assertEqual(replay(state, edit), child)
                for f, queue in enumerate(child.queues):
                    self.assertTrue(queue)
                    for j in queue:
                        self.assertTrue(0 <= child.resources[j][0] < dims[f][0])
                        self.assertTrue(0 <= child.resources[j][1] < dims[f][1])

    def test_swap_support_v9_resource_rebinding(self):
        old = Space(3).state(137)
        state = State.from_genome(old.genome(), 2)
        expected = {State.from_genome(c.genome(), 2) for c in labelled_children(old, "swap_rebind")}
        actual = set()
        for a in state.queues[0]:
            for b in state.queues[1]:
                for ma in range(2):
                    for wa in range(2):
                        for mb in range(2):
                            for wb in range(2):
                                actual.add(replay(state, {"family": "swap_rebind", "jobs": [a,b], "resources": [(ma,wa),(mb,wb)]}))
        self.assertEqual(actual, expected)

    def test_real_calls_replay_trace_and_fixed_seed(self):
        instance = make_instance(3, 17417)
        params = parameters(instance, 17417)[0]["strong_fast"]
        state = State.from_genome(Space(3).state(137).genome(), 2)
        with patch("research.fatigue_scale.chain.decode", wraps=decode) as counted:
            result = run(instance, params, state, "mix_alternate", 60013, [0,1,0], "FE")
        self.assertEqual(counted.call_count, 65)
        self.assertEqual(Counter(r["family"] for r in result["steps"]), {"plain":32, "swap_rebind":32})
        other = run(instance, params, state, "mix_alternate", 60013, [0,1,0], "FE")
        self.assertEqual(result["final_state"], other["final_state"])
        for step in result["steps"]:
            child = replay(state, step["edit"])
            _validate_genome(instance, child.genome())
            if step["accepted"]:
                state = child

    def test_deadline_excludes_paid_late_improvement(self):
        instance = make_instance(3, 17417)
        params = parameters(instance, 17417)[0]["beta0"]
        state = State.from_genome(Space(3).state(137).genome(), 2)
        parent = decode(instance, state.genome(), params)
        fake = SimpleNamespace(objectives=parent.objectives*.5)
        ticks = iter((0,0,2_000_000_000,3_000_000_000,4_000_000_000))
        with patch("research.fatigue_scale.chain.decision", return_value=({"improves":True},state,fake)):
            result = run(instance, params, state, "mix_iid", 1, [0,1,0], "time", 1., clock=lambda:next(ticks))
        self.assertEqual(result["full_decodes"], 2)
        self.assertEqual(result["gain"], 0.)


if __name__ == "__main__":
    unittest.main()
