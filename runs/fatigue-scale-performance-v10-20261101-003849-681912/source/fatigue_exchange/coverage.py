"""Exact physical endpoint coverage and true labelled proposal probabilities."""
import numpy as np
from research.fatigue_coordination.controls import exact_probability
from .operators import labelled_children


def n2_endpoints(graph, parent):
    values = []
    for first in range(graph.space.jobs):
        for middle in graph.neighbors(parent, first):
            values.extend(graph.neighbors(middle, second) for second in range(graph.space.jobs) if second != first)
    return np.unique(np.concatenate(values))


def row(values, parent, labels, n2, total_improving, epsilon):
    unique = np.unique(labels)
    improved = values[unique] < values[parent]-epsilon
    probability = float(np.mean(values[labels] < values[parent]-epsilon))
    in_n2 = np.isin(unique, n2)
    return {"labelled_outcomes": len(labels), "unique_endpoints": len(unique),
        "improving_endpoints": int(improved.sum()), "can_improve": bool(improved.any()),
        "outside_N2_endpoints": int((~in_n2).sum()),
        "improving_N2_coverage": float(np.sum(improved & in_n2)/total_improving) if total_improving else None,
        "best_gain": float(max(0, values[parent]-values[unique].min())),
        "one_draw_success": probability, "p16": float(1-(1-probability)**16)}


def evaluate(graph, tables, reference, analyses, identity, emit):
    eligible = np.flatnonzero(np.logical_or.reduce([a["strict"] for a in analyses]))
    all_pairs = tuple((a, b) for a in range(graph.space.jobs) for b in range(graph.space.jobs) if a != b)
    for parent in eligible:
        state = graph.space.state(int(parent))
        n2 = n2_endpoints(graph, parent)
        pools = {kind: np.asarray([graph.space.index(c) for c in labelled_children(state, kind)])
                 for kind in ("rebind", "swap", "swap_rebind")}
        for kind in ("swap", "swap_rebind"):
            assert np.isin(pools[kind], n2).all(), (kind, int(parent))
        for mi, model in enumerate(("beta0", "strong_fast", "strong_slow")):
            values = tables[mi, :, 1]/reference[1]
            improving = int(np.sum(values[n2] < values[parent]-1e-10))
            distribution = exact_probability(graph, values, int(parent), "plain_composite", all_pairs, 1e-10, 16)
            emit("coverage", {**identity, "parent": int(parent), "model": model, "method": "plain",
                "parent_strict": bool(analyses[mi]["strict"][parent]), "unique_endpoints": len(n2),
                "improving_endpoints": improving, "can_improve": improving > 0,
                "improving_N2_coverage": 1. if improving else None,
                "best_gain": float(max(0, values[parent]-values[n2].min())),
                "one_draw_success": distribution["one_draw_success"], "p16": distribution["budget_success"]})
            for kind, ids in pools.items():
                emit("coverage", {**identity, "parent": int(parent), "model": model, "method": kind,
                    "parent_strict": bool(analyses[mi]["strict"][parent]), **row(values, parent, ids, n2, improving, 1e-10)})
    return eligible
