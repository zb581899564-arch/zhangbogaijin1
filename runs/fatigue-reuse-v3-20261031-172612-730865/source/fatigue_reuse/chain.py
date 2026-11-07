"""Small local chains with actual deadlines, cache epochs and measured costs."""
from dataclasses import asdict
from time import perf_counter_ns
import numpy as np
from research.fatigue_mechanism.decoder import decode
from research.fatigue_mechanism.statistics import select_minima
from .neighbors import local_pool
from . import scorer


def timed(phases, name, function, *args, **kwargs):
    start = perf_counter_ns()
    value = function(*args, **kwargs)
    phases[name] = phases.get(name, 0) + perf_counter_ns() - start
    return value


def run(instance, params, initial, weights, method, mode, protocol, pool_seed, choice_seed,
        refresh_every_step=False):
    """Data loading/JSON disk writes are outside; all local search work is inside."""
    started = perf_counter_ns()
    phases, rows, epochs = {}, [], []
    rng = np.random.default_rng(choice_seed)
    parent = timed(phases, "initial_decode", decode, instance, initial, params, method != "random")
    genome, scales = initial, parent.objectives.copy()
    effective = np.asarray(weights) / scales
    initial_value = float(parent.objectives @ effective)
    cache, epoch, version, accepted, partial_calls = None, None, 0, 0, 0
    budget_ns = int(protocol["time_budget_seconds"] * 1e9) if mode == "time" else None
    while True:
        step = len(rows)
        if mode == "steps" and step >= protocol["decisions"]:
            break
        if budget_ns is not None and perf_counter_ns() - started >= budget_ns:
            break
        candidate_seed = pool_seed + step * 1000003
        pool = timed(phases, "generation", local_pool, instance, genome, candidate_seed, protocol["candidate_count"])
        before_version, before_value = version, float(parent.objectives @ effective)
        scores, stage0_ns = None, 0
        if method != "random":
            if cache is None or refresh_every_step:
                if epoch is not None:
                    epoch["closed_reason"] = "forced_refresh"
                cache = timed(phases, "cache_build", scorer.build, instance, params, genome, parent,
                              method, weights, scales, version)
                epoch = {"epoch": len(epochs), "version": version, "born_step": step,
                         "uses": 0, "on_time_uses": 0, "closed_reason": None}
                epochs.append(epoch)
            scores, partials, stage0_ns = timed(phases, "scoring", scorer.scores, instance, params,
                                               genome, parent, pool, cache, version)
            partial_calls += partials
            epoch["uses"] += 1
        selection_start = perf_counter_ns()
        support = np.arange(len(pool)) if scores is None else select_minima(scores)
        chosen = int(support[int(rng.integers(len(support)))])
        phases["selection"] = phases.get("selection", 0) + perf_counter_ns() - selection_start
        candidate = pool[chosen]
        child = timed(phases, "child_decode", decode, instance, candidate.genome, params, method != "random")
        child_value = float(child.objectives @ effective)
        completed_ns = perf_counter_ns() - started
        on_time = budget_ns is None or completed_ns <= budget_ns
        improve = before_value - child_value > 1e-10
        did_accept = bool(improve and on_time)
        if epoch is not None and on_time:
            epoch["on_time_uses"] += 1
        row = {"step": step, "parent_version": before_version, "pool_seed": candidate_seed,
               "chosen_index": chosen, "kind": candidate.kind, "jobs": candidate.jobs,
               "chosen_genome": asdict(candidate.genome), "child_objectives": child.objectives.tolist(),
               "before_value": before_value, "child_value": child_value, "would_improve": bool(improve),
               "on_time": bool(on_time), "accepted": did_accept, "evaluation_completed_ns": completed_ns,
               "score_support": support.tolist(), "scores": None if scores is None else scores.tolist(),
               "cache_epoch": None if epoch is None else epoch["epoch"], "stage0_ns": stage0_ns}
        rows.append(row)
        if did_accept:
            accepted += 1
            genome, parent, version = candidate.genome, child, version + 1
            if epoch is not None:
                epoch["closed_reason"] = "accepted"
            cache, epoch = None, None
    if epoch is not None:
        epoch["closed_reason"] = "terminal_right_censored"
    final_objectives = parent.objectives.copy()
    final_value = float(final_objectives @ effective)
    finished_ns = perf_counter_ns() - started
    actual_uses = sum(e["uses"] for e in epochs)
    summary = {"method": method, "mode": mode, "refresh_every_step": refresh_every_step,
               "initial_objectives": scales.tolist(), "final_objectives": final_objectives.tolist(),
               "initial_value": initial_value, "final_value": final_value, "gain": initial_value - final_value,
               "elapsed_ns": finished_ns, "deadline_ns": budget_ns,
               "overrun_ns": max(0, finished_ns - budget_ns) if budget_ns is not None else 0,
               "attempted_decisions": len(rows), "on_time_decisions": sum(r["on_time"] for r in rows),
               "accepted": accepted, "full_decodes": 1 + len(rows), "partial_stage0_calls": partial_calls,
               "cache_builds": len(epochs), "cache_uses": actual_uses,
               "reuse_hits": actual_uses - len(epochs), "actual_q": actual_uses / len(epochs) if epochs else None,
               "phases_ns": phases, "stage0_ns": sum(r["stage0_ns"] for r in rows),
               "bookkeeping_ns": finished_ns - sum(phases.values()), "final_genome": asdict(genome)}
    return summary, rows, epochs
