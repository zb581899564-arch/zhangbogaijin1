"""General-resource local runner; every candidate pays the same full decoder."""
from collections import Counter
from dataclasses import asdict
from time import perf_counter_ns
import numpy as np
from research.fatigue_mechanism.decoder import decode
from research.fatigue_mixture.policy import family
from .operators import dimensions, draw


def timed(phases, name, function, *args, **kwargs):
    started = perf_counter_ns()
    result = function(*args, **kwargs)
    phases[name] += perf_counter_ns()-started
    return result


def decision(instance, params, state, parent, method, step, seeds, dims, effective, phases):
    selected = family(method, step, seeds["branch"])
    proposal_seed = seeds["proposal"]+1000003*step
    child_state, edit = timed(phases, "generation", draw, state, selected, dims, proposal_seed)
    child = timed(phases, "child_decode", decode, instance, child_state.genome(), params, retain_trace=False)
    before, after = float(parent.objectives @ effective), float(child.objectives @ effective)
    row = {"step": step, "family": selected, "proposal_seed": proposal_seed, "edit": edit,
        "objectives": child.objectives.tolist(), "before": before, "after": after,
        "load_counts_changed": child_state.counts() != state.counts(),
        "improves": before-after > 1e-10, "noop": child_state == state}
    return row, child_state, child


def run(instance, params, initial, method, rng_seed, weights, mode, seconds=None, children=64, clock=perf_counter_ns):
    started = clock()
    phases, rows, accepted = Counter(), [], 0
    seeds = {"branch": rng_seed+291827, "proposal": rng_seed+72913}
    deadline = int(seconds*1e9) if mode == "time" else None
    dims, state = dimensions(instance), initial
    parent = timed(phases, "parent_decode", decode, instance, state.genome(), params, retain_trace=False)
    scales = parent.objectives.copy()
    effective = np.asarray(weights)/scales
    initial_value = float(parent.objectives @ effective)
    while (len(rows) < children if deadline is None else clock()-started < deadline):
        row, child_state, child = decision(instance, params, state, parent, method, len(rows), seeds, dims, effective, phases)
        row.update({"accepted": False, "on_time": False, "completed_ns": 0})
        rows.append(row)
        completed = clock()-started
        on_time = deadline is None or completed <= deadline
        row.update({"on_time": on_time, "completed_ns": completed})
        if on_time and row["improves"]:
            old = state, parent
            state, parent = child_state, child
            committed = clock()-started
            if deadline is not None and committed > deadline:
                state, parent = old
                row.update({"on_time": False, "completed_ns": committed})
            else:
                accepted += 1
                row.update({"accepted": True, "completed_ns": committed})
    finished = clock()-started
    gain = initial_value-float(parent.objectives @ effective)
    return {"method": method, "rng_seed": rng_seed, "streams": seeds, "mode": mode, "seconds": seconds,
        "initial_state": asdict(initial), "final_state": asdict(state), "initial_objectives": scales.tolist(),
        "final_objectives": parent.objectives.tolist(), "weights": weights, "gain": gain,
        "gain_per_second": gain/(finished/1e9), "elapsed_ns": finished, "deadline_ns": deadline,
        "overrun_ns": max(0, finished-deadline) if deadline else 0, "full_decodes": 1+len(rows),
        "partial_calls": 0, "accepted": accepted, "phases_ns": dict(phases),
        "bookkeeping_ns": finished-sum(phases.values()), "steps": rows}
