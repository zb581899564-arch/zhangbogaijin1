"""Mixtures preserve ordinary N2 support and reweight its proposal mass."""
import numpy as np
from research.fatigue_coordination.controls import exact_probability
from research.fatigue_exchange.coverage import n2_endpoints
from research.fatigue_exchange.operators import labelled_children


def probabilities(plain, swap, method, draws):
    if method == "mix_alternate":
        assert draws % 2 == 0
        return 1-(1-plain)**(draws//2)*(1-swap)**(draws//2)
    p = plain if method == "plain" else swap if method == "swap_rebind" else (plain+swap)/2
    return 1-(1-p)**draws


def evaluate(graph, tables, reference, analyses, identity, emit):
    eligible = np.flatnonzero(np.logical_or.reduce([a["strict"] for a in analyses]))
    pairs = tuple((a, b) for a in range(4) for b in range(4) if a != b)
    for parent in eligible:
        n2 = n2_endpoints(graph, parent)
        swaps = np.array([graph.space.index(s) for s in labelled_children(graph.space.state(parent), "swap_rebind")])
        assert len(swaps) == len(np.unique(swaps)) and np.isin(swaps, n2).all()
        for mi, model in enumerate(("beta0", "strong_fast", "strong_slow")):
            values = tables[mi, :, 1]/reference[1]
            threshold = values[parent]-1e-10
            p_plain = exact_probability(graph, values, int(parent), "plain_composite", pairs, 1e-10, 16)["one_draw_success"]
            p_swap = float(np.mean(values[swaps] < threshold))
            total = int(np.sum(values[n2] < threshold))
            for method in ("plain", "swap_rebind", "mix_iid", "mix_alternate"):
                support = swaps if method == "swap_rebind" else n2
                improving = int(np.sum(values[support] < threshold))
                emit("coverage", {**identity, "parent": int(parent), "model": model, "method": method,
                    "parent_strict": bool(analyses[mi]["strict"][parent]), "p_plain": p_plain, "p_swap": p_swap,
                    "p16": probabilities(p_plain, p_swap, method, 16), "p32": probabilities(p_plain, p_swap, method, 32),
                    "unique_endpoints": len(support), "improving_endpoints": improving, "can_improve": improving > 0,
                    "improving_N2_coverage": improving/total if total else None,
                    "best_gain": float(max(0, values[parent]-values[support].min()))})
    return eligible
