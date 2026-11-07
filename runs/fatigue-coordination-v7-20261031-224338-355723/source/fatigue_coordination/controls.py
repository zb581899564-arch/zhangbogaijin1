"""Live ordinary moves; census/graph values are never input to timed trials."""
from dataclasses import asdict
from time import perf_counter_ns
import math
import numpy as np
from research.fatigue_mechanism.decoder import decode, _validate_genome
from .space import moves


def pairs_from_trace(jobs, trace, kind):
    all_pairs = tuple((a, b) for a in range(jobs) for b in range(jobs) if a != b)
    if kind == "plain_composite":
        return all_pairs, False
    role = 1 if kind == "machine_pair" else 2
    linked = set()
    for op in trace.operations:
        predecessor = op.parents[role]
        if predecessor >= 0:
            other = predecessor % jobs
            linked.update(((op.job, other), (other, op.job)))
    return tuple(sorted(linked)) if linked else all_pairs, not bool(linked)


def run_trial(instance, params, state, weights, reference, kind, seed, budget):
    started = perf_counter_ns()
    rng = np.random.default_rng(seed)
    needs_trace = kind in ("machine_pair", "worker_pair")
    parent = decode(instance, state.genome(), params, retain_trace=needs_trace)
    pairs, fallback = ((), False) if kind == "single_job" else pairs_from_trace(instance.jobs, parent, kind)
    effective = np.asarray(weights)/reference
    before = best = float(parent.objectives @ effective)
    best_state, best_objectives, rows = state, parent.objectives.tolist(), []
    for draw in range(budget):
        if kind == "single_job":
            first, second = int(rng.integers(instance.jobs)), None
        else:
            first, second = pairs[int(rng.integers(len(pairs)))]
        choices = moves(state, first)
        middle = choices[int(rng.integers(len(choices)))]
        if second is None:
            child_state = middle
        else:
            choices = moves(middle, second)
            child_state = choices[int(rng.integers(len(choices)))]
        _validate_genome(instance, middle.genome())
        child = decode(instance, child_state.genome(), params, retain_trace=False)
        value = float(child.objectives @ effective)
        if value < best:
            best, best_state, best_objectives = value, child_state, child.objectives.tolist()
        rows.append({"draw": draw, "first_job": first, "second_job": second, "middle": asdict(middle),
                     "child": asdict(child_state), "objectives": child.objectives.tolist(), "value": value})
    finished = perf_counter_ns()-started
    return {"method": kind, "seed": seed, "full_decodes": 1+budget, "elapsed_ns": finished,
        "before_value": before, "best_value": best, "gain": before-best, "pairs": pairs,
        "fallback": fallback, "best_state": asdict(best_state), "best_objectives": best_objectives, "rows": rows}


def exact_probability(graph, values, state, kind, pairs, epsilon, budget):
    threshold, endpoints, probability = values[state]-epsilon, set(), 0.
    if kind == "single_job":
        for job in range(graph.space.jobs):
            candidates = graph.neighbors(state, job)
            probability += float(np.mean(values[candidates] < threshold))/graph.space.jobs
            endpoints.update(map(int, candidates))
    else:
        for first, second in pairs:
            middle = graph.neighbors(state, first)
            for mid in middle:
                candidates = graph.neighbors(mid, second)
                probability += float(np.mean(values[candidates] < threshold))/(len(pairs)*len(middle))
                endpoints.update(map(int, candidates))
    probability = min(1., max(0., probability))
    success = 1. if probability == 1 else -math.expm1(budget*math.log1p(-probability))
    return {"one_draw_success": probability, "budget_success": success, "unique_endpoints": len(endpoints),
            "unique_improving_endpoints": sum(values[i] < threshold for i in endpoints),
            "noop_endpoint_in_pool": state in endpoints}
