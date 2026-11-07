"""Initial-pool component costs, with independent numerical equivalence checks."""
from collections import Counter
import numpy as np
from research.fatigue_mechanism.decoder import decode
from research.fatigue_mechanism.timing import measure
from research.fatigue_topology.trials import local_pool as reference_pool
from research.fatigue_topology.counterfactual import stage0 as reference_stage0
from .neighbors import local_pool
from .stage0 import exact_stage0


def calibrate(instance, params, genome, seed, count=16):
    calls, arrays = Counter(), params.arrays(instance)
    pool = local_pool(instance, genome, seed, count)
    assert pool == reference_pool(instance, genome, seed, count), "candidate stream changed"

    def fast(candidate):
        calls["fast_stage0"] += 1
        return exact_stage0(instance, candidate.genome, arrays)

    def reference(candidate):
        calls["reference_stage0"] += 1
        return reference_stage0(instance, candidate.genome, params)

    for candidate in pool:
        new, old = fast(candidate), reference(candidate)
        np.testing.assert_array_equal(new.C, old.C[:instance.jobs])
        np.testing.assert_array_equal(new.v, old.v[:instance.jobs])
        np.testing.assert_allclose(new.direct, [0., old.energy, old.labor], atol=1e-10, rtol=1e-12)

    def full(retain_trace):
        calls["trace_full" if retain_trace else "plain_full"] += 1
        return decode(instance, genome, params, retain_trace)

    values = {"fast_stage0_pool": measure(lambda: [fast(c) for c in pool], 5),
              "reference_stage0_pool": measure(lambda: [reference(c) for c in pool], 5),
              "generation": measure(lambda: local_pool(instance, genome, seed, count), 5),
              "plain_full": measure(lambda: full(False), 5), "trace_full": measure(lambda: full(True), 5)}
    return {"component_timings": values, "calls": dict(calls), "candidates_verified": len(pool)}
