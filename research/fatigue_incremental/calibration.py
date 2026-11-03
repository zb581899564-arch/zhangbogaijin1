"""Exact numerical/work equivalence and predeclared component timings."""
from collections import Counter
import numpy as np
from research.fatigue_mechanism.decoder import decode
from research.fatigue_mechanism.timing import measure
from research.fatigue_reuse.neighbors import local_pool
from research.fatigue_reuse.stage0 import exact_stage0
from .prefix import build_prefix, incremental_stage0


def calibrate(instance, params, genome, seed, count=16):
    calls, arrays = Counter(), params.arrays(instance)
    parent = decode(instance, genome, params)
    calls["parent_trace_full"] += 1
    prefix = build_prefix(instance, genome, parent)
    calls["prefix_build"] += 1
    pool = local_pool(instance, genome, seed, count)
    work_total = Counter()

    def incremental(candidate):
        calls["incremental_stage0"] += 1
        value, work = incremental_stage0(instance, candidate.genome, arrays, prefix)
        work_total.update(work)
        return value

    def full(candidate):
        calls["full_stage0"] += 1
        return exact_stage0(instance, candidate.genome, arrays)

    def prefix_build():
        calls["prefix_build"] += 1
        return build_prefix(instance, genome, parent)

    def complete(trace):
        calls["trace_full" if trace else "plain_full"] += 1
        return decode(instance, genome, params, trace)

    for candidate in pool:
        new, old = incremental(candidate), full(candidate)
        for name in ("C", "v", "direct"):
            np.testing.assert_array_equal(getattr(new, name), getattr(old, name))
    values = {"incremental_stage0_pool": measure(lambda: [incremental(c) for c in pool], 5),
              "full_stage0_pool": measure(lambda: [full(c) for c in pool], 5),
              "prefix_build": measure(prefix_build, 5),
              "generation": measure(lambda: local_pool(instance, genome, seed, count), 5),
              "plain_full": measure(lambda: complete(False), 5), "trace_full": measure(lambda: complete(True), 5)}
    return {"component_timings": values, "calls": dict(calls), "work": dict(work_total),
            "candidates_verified": len(pool), "C_v_direct_bitwise_equal": True}
