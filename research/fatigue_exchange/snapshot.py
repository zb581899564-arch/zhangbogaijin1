"""Identical candidates and paid truths, never fed to an online chain."""
from dataclasses import asdict
from time import perf_counter_ns
import numpy as np
from research.fatigue_mechanism.decoder import decode
from research.fatigue_mechanism.statistics import select_minima
from .operators import pool
from . import scoring


def evaluate(instance, params, state, rng_seed, counts):
    started = perf_counter_ns()
    parent = decode(instance, state.genome(), params)
    candidates = pool(state, "swap_rebind", rng_seed+72913, 8)
    methods = {}
    for method in ("pool_cheap", "pool_time", "pool_fatigue"):
        begin = perf_counter_ns()
        cache = scoring.build(instance, params, state, parent, method, parent.objectives, 0)
        scores, calls, stage_ns = scoring.scores(instance, params, state, parent, candidates, cache, method, 0)
        support = select_minima(scores)
        rng = np.random.default_rng(rng_seed+145907)
        chosen = int(support[int(rng.integers(len(support)))])
        methods[method] = {"scores": scores.tolist(), "chosen": chosen, "score_ns": perf_counter_ns()-begin,
                           "partial_calls": calls, "stage0_ns": stage_ns}
    rng = np.random.default_rng(rng_seed+145907)
    methods["pool_random"] = {"chosen": int(rng.integers(8)), "partial_calls": 0}
    truth = np.array([decode(instance, c.genome, params, retain_trace=False).objectives for c in candidates])
    gains = 1-truth[:, 1]/parent.objectives[1]
    oracle = max(0., float(gains.max()))
    for record in methods.values():
        gain = max(0., float(gains[record["chosen"]]))
        record.update({"selected_gain": gain, "oracle_regret": oracle-gain})
    counts["snapshot_full"] += 9
    counts["snapshot_partial"] += sum(v["partial_calls"] for v in methods.values())
    counts["snapshot_ns"] += perf_counter_ns()-started
    return {"rng_seed": rng_seed, "parent_objectives": parent.objectives.tolist(),
            "candidates": [asdict(c.state) for c in candidates], "objectives": truth.tolist(),
            "methods": methods, "oracle_gain": oracle}
