"""One full child per decision; a minimal shared runner for all four policies."""
from collections import Counter
from dataclasses import asdict
from time import perf_counter_ns
from research.fatigue_mechanism.decoder import decode
from .policy import candidate


def timed(phases, name, function, *args, **kwargs):
    started = perf_counter_ns()
    result = function(*args, **kwargs)
    phases[name] += perf_counter_ns()-started
    return result


def decision(instance, params, state, parent, method, step, seeds, scale, phases):
    selected, proposal_seed, child_state = timed(phases, "generation", candidate, state, method, step, seeds)
    child = timed(phases, "child_decode", decode, instance, child_state.genome(), params, retain_trace=False)
    before, after = float(parent.objectives[1]/scale), float(child.objectives[1]/scale)
    row = {"step": step, "family": selected, "proposal_seed": proposal_seed,
        "child_state": asdict(child_state), "objectives": child.objectives.tolist(),
        "before": before, "after": after, "improves": before-after > 1e-10,
        "load_counts_changed": len(child_state.queues[0]) != len(state.queues[0]), "partial_calls": 0}
    return row, child_state, child


def run(instance, params, initial, method, rng_seed, mode, seconds=None, clock=perf_counter_ns):
    started = clock()
    phases, rows, accepted = Counter(), [], 0
    seeds = {"branch": rng_seed+291827, "proposal": rng_seed+72913}
    deadline = int(seconds*1e9) if mode == "time" else None
    state = initial
    parent = timed(phases, "parent_decode", decode, instance, state.genome(), params, retain_trace=False)
    scales = parent.objectives.copy()
    while (len(rows) < 32 if deadline is None else clock()-started < deadline):
        row, child_state, child = decision(instance, params, state, parent, method, len(rows), seeds, scales[1], phases)
        row.update({"accepted": False, "on_time": False, "completed_ns": 0})
        rows.append(row)
        completed = clock()-started
        on_time = deadline is None or completed <= deadline
        row.update({"on_time": on_time, "completed_ns": completed})
        if on_time and row["improves"]:
            previous = state, parent
            state, parent = child_state, child
            committed = clock()-started
            if deadline is not None and committed > deadline:
                state, parent = previous
                row.update({"on_time": False, "completed_ns": committed})
            else:
                accepted += 1
                row.update({"accepted": True, "completed_ns": committed})
    finished = clock()-started
    return {"method": method, "rng_seed": rng_seed, "streams": seeds, "mode": mode, "seconds": seconds,
        "initial_state": asdict(initial), "final_state": asdict(state), "initial_objectives": scales.tolist(),
        "final_objectives": parent.objectives.tolist(), "gain": float(1-parent.objectives[1]/scales[1]),
        "elapsed_ns": finished, "deadline_ns": deadline, "overrun_ns": max(0, finished-deadline) if deadline else 0,
        "full_decodes": 1+len(rows), "partial_calls": 0, "accepted": accepted,
        "on_time_children": sum(r["on_time"] for r in rows), "phases_ns": dict(phases),
        "bookkeeping_ns": finished-sum(phases.values()), "steps": rows}
