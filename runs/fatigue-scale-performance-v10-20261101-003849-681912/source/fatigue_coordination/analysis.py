"""Exact N1/N2 minima and neutral-plateau classification, no search policy."""
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components


def minima(graph, values):
    n = graph.space.jobs
    by_job = np.minimum.reduceat(values[graph.destination], graph.pointer[:-1]).reshape(-1, n)
    order = np.argsort(by_job, axis=1, kind="stable")
    first = np.take_along_axis(by_job, order[:, :1], axis=1)
    second = np.take_along_axis(by_job, order[:, 1:2], axis=1)
    excluding = np.where(np.arange(n)[None, :] == order[:, :1], second, first)
    two_step = excluding[graph.destination, graph.job]
    best_two = np.minimum.reduceat(two_step, graph.row_pointer[:-1])
    return by_job, by_job.min(axis=1), best_two


def plateaus(graph, values, best_one, best_two, epsilon):
    source, destination = graph.source, graph.destination
    flat = np.abs(values[destination]-values[source]) <= epsilon
    sparse = csr_matrix((np.ones(int(flat.sum()), dtype=bool), (source[flat], destination[flat])),
                        shape=(len(values), len(values)))
    count, labels = connected_components(sparse, directed=False)
    lower = np.full(count, np.inf)
    upper = np.full(count, -np.inf)
    np.minimum.at(lower, labels, values)
    np.maximum.at(upper, labels, values)
    exits = np.zeros(count, dtype=bool)
    np.logical_or.at(exits, labels[source], values[destination] < values[source]-epsilon)
    certified = upper-lower <= epsilon
    local = best_one >= values-epsilon
    weak = local & (best_two < values-epsilon)
    strict = weak & ~exits[labels] & certified[labels]
    summary = {"states": len(values), "global_optimum": float(values.min()),
        "global_states": int(np.sum(values <= values.min()+epsilon)), "N1_local_states": int(local.sum()),
        "suboptimal_N1_local_states": int(np.sum(local & (values > values.min()+epsilon))),
        "weak_N2_states": int(weak.sum()), "strict_N2_states": int(strict.sum()),
        "weak_with_neutral_exit": int(np.sum(weak & exits[labels])),
        "weak_in_uncertain_plateau": int(np.sum(weak & ~certified[labels])),
        "flat_components": count, "closed_suboptimal_components": int(np.sum(~exits & certified & (lower > values.min()+epsilon))),
        "strict_components": len(np.unique(labels[strict])), "maximum_plateau_span": float((upper-lower).max())}
    return {"best_one": best_one, "best_two": best_two, "N1_local": local, "weak": weak,
            "strict": strict, "component": labels, "component_lower": lower, "component_upper": upper,
            "component_lower_exit": exits, "component_certified": certified, "summary": summary}


def analyze(graph, values, epsilon):
    by_job, one, two = minima(graph, values)
    result = plateaus(graph, values, one, two, epsilon)
    result["by_job"] = by_job
    return result


def best_path(graph, values, analysis, state):
    best, path = np.inf, None
    for first in range(graph.space.jobs):
        middle = graph.neighbors(state, first)
        costs = analysis["by_job"][middle].copy()
        costs[:, first] = np.inf
        pos, second = np.unravel_index(int(np.argmin(costs)), costs.shape)
        if costs[pos, second] < best:
            mid = int(middle[pos])
            endings = graph.neighbors(mid, int(second))
            end = int(endings[np.argmin(values[endings])])
            best, path = float(values[end]), (int(first), mid, int(second), end)
    assert best == analysis["best_two"][state]
    return path


def paired_counts(baseline, dynamic):
    result = {}
    for name in ("weak", "strict"):
        a, b = baseline[name], dynamic[name]
        result[name] = {"beta0_only": int(np.sum(a & ~b)), "dynamic_only": int(np.sum(b & ~a)),
                        "both": int(np.sum(a & b)), "neither": int(np.sum(~a & ~b))}
    return result
