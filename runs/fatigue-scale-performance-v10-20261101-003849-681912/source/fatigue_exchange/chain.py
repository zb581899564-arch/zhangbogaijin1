"""Isolated monotone local chains with paid full FE and real deadlines."""
from dataclasses import asdict
from time import perf_counter_ns
from collections import Counter
import numpy as np
from research.fatigue_mechanism.decoder import decode
from research.fatigue_mechanism.statistics import select_minima
from .operators import pool
from . import scoring


def timed(phases, name, function, *args, **kwargs):
    started = perf_counter_ns()
    result = function(*args, **kwargs)
    phases[name] += perf_counter_ns()-started
    return result


def decide(instance, params, state, parent, cache, version, method, scales, seeds, step, phases):
    scored = method in ("pool_cheap", "pool_time", "pool_fatigue")
    operator = "swap_rebind" if method.startswith("pool_") else method
    size = 8 if method.startswith("pool_") else 1
    pool_seed = seeds["pool"]+1000003*step
    candidates = timed(phases, "generation", pool, state, operator, pool_seed, size)
    predictions, partials, stage_ns = None, 0, 0
    if scored:
        if cache is None:
            cache = timed(phases, "cache_build", scoring.build, instance, params, state, parent, method, scales, version)
            phases["cache_builds"] += 1
        predictions, partials, stage_ns = timed(phases, "scoring", scoring.scores,
            instance, params, state, parent, candidates, cache, method, version)
    chooser = np.random.default_rng(seeds["choice"]+1000003*step)
    support = np.arange(size) if predictions is None else select_minima(predictions)
    chosen = int(support[int(chooser.integers(len(support)))])
    child_state = candidates[chosen].state
    child = timed(phases, "child_decode", decode, instance, child_state.genome(), params, retain_trace=scored)
    before, after = float(parent.objectives[1]/scales[1]), float(child.objectives[1]/scales[1])
    row = {"step": step, "pool_seed": pool_seed, "pool_size": size, "chosen": chosen,
           "scores": None if predictions is None else predictions.tolist(), "support": support.tolist(),
           "child_state": asdict(child_state), "objectives": child.objectives.tolist(),
           "before": before, "after": after, "partial_calls": partials, "stage0_ns": stage_ns,
           "version": version, "improves": before-after > 1e-10}
    return row, child_state, child, cache


def run(instance, params, initial, method, rng_seed, mode, seconds=None, clock=perf_counter_ns):
    started = clock()
    phases, rows = Counter(), []
    seeds = {"pool": rng_seed+72913, "choice": rng_seed+145907}
    deadline = int(seconds*1e9) if mode == "time" else None
    scored = method in ("pool_cheap", "pool_time", "pool_fatigue")
    state, version, cache = initial, 0, None
    parent = timed(phases, "parent_decode", decode, instance, state.genome(), params, retain_trace=scored)
    scales = parent.objectives.copy()
    while (len(rows) < 32 if deadline is None else clock()-started < deadline):
        row, child_state, child, next_cache = decide(instance, params, state, parent, cache,
            version, method, scales, seeds, len(rows), phases)
        row.update({"accepted": False, "on_time": False, "completed_ns": 0})
        rows.append(row)
        completed = clock()-started
        on_time = deadline is None or completed <= deadline
        row.update({"on_time": on_time, "completed_ns": completed})
        if on_time and row["improves"]:
            old = (state, parent, version, cache)
            state, parent, version, cache = child_state, child, version+1, None
            committed = clock()-started
            if deadline is not None and committed > deadline:
                state, parent, version, cache = old
                row.update({"on_time": False, "completed_ns": committed})
            else:
                row.update({"accepted": True, "completed_ns": committed})
        else:
            cache = next_cache
    finished = clock()-started
    phase_ns = {k: v for k, v in phases.items() if k != "cache_builds"}
    return {"method": method, "rng_seed": rng_seed, "mode": mode, "seconds": seconds,
        "initial_state": asdict(initial), "final_state": asdict(state), "initial_objectives": scales.tolist(),
        "final_objectives": parent.objectives.tolist(), "gain": float(1-parent.objectives[1]/scales[1]),
        "elapsed_ns": finished, "deadline_ns": deadline, "overrun_ns": max(0, finished-deadline) if deadline else 0,
        "full_decodes": 1+len(rows), "partial_calls": sum(r["partial_calls"] for r in rows),
        "stage0_ns": sum(r["stage0_ns"] for r in rows), "cache_builds": phases["cache_builds"],
        "accepted": version, "on_time_children": sum(r["on_time"] for r in rows),
        "phases_ns": phase_ns, "bookkeeping_ns": finished-sum(phase_ns.values()), "steps": rows}
