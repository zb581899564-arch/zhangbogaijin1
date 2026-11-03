"""Keep selector gains separate from donor quality and candidate legality."""
from collections import defaultdict
import numpy as np
from .statistics import paired, adjust_primary, CONTRASTS
from .protocol import PROTOCOL


def means(rows):
    fields = ("gain", "elapsed_ns", "overrun_ns", "on_time_decisions", "accepted", "full_decodes", "teacher_full_decodes", "partial_calls")
    wall = sum(r["elapsed_ns"] for r in rows)
    phases = sorted({name for r in rows for name in r["phases_ns"]})
    return {**{f: float(np.mean([r[f] for r in rows])) for f in fields},
        "gain_per_second": float(np.mean([r["gain"]/(r["elapsed_ns"]/1e9) for r in rows])),
        "mean_objective_gains": np.mean([1-np.asarray(r["final_objectives"])/r["initial_objectives"] for r in rows], axis=0).tolist(),
        "phase_time_fractions": {name: sum(r["phases_ns"].get(name, 0) for r in rows)/wall for name in phases},
        "stage0_time_fraction": sum(r["stage0_ns"] for r in rows)/wall,
        "mean_teacher_best_value": float(np.mean([min(r["teacher_values"]) for r in rows])),
        "teacher_better_than_receiver_fraction": float(np.mean([min(r["teacher_values"]) < 1-1e-10 for r in rows]))}


def summarize(chains, mechanisms, completion):
    cells = defaultdict(list)
    for row in chains:
        row["gain_per_second"] = row["gain"]/(row["elapsed_ns"]/1e9)
        cells[row["mode"], row["target"], row["regime"], row["block_size"]].append(row)
    groups, comparisons, rates = [], [], []
    for (mode, target, regime, size), rows in sorted(cells.items()):
        identity = {"mode": mode, "target": target, "regime": regime, "block_size": size}
        methods = [{"method": m, "runs": len(rows)//5, **means([r for r in rows if r["method"] == m])} for m in PROTOCOL["methods"]]
        groups.append({**identity, "methods": methods})
        comparisons.extend({**identity, **paired(rows, a, b)} for a, b in CONTRASTS)
        if target == "TEC" and regime == "fixed_FA" and size == 2:
            rates.extend({**identity, **paired(rows, a, b, "gain_per_second")} for a, b in PROTOCOL["primary"]["comparisons"])
    primary = adjust_primary(comparisons)
    snapshot = []
    grouped = defaultdict(list)
    for row in mechanisms:
        grouped[row["target"], row["regime"], row["block_size"]].append(row)
    for (target, regime, size), pools in sorted(grouped.items()):
        selectors = []
        for method in PROTOCOL["methods"]:
            selected = [v for pool in pools for v in pool["selection"] if v["method"] == method]
            value = {"method": method}
            for field in ("realized_gain", "accepted_gain", "oracle_regret", "rank_spearman", "mean_abs_prediction_error"):
                valid = [r[field] for r in selected if r[field] is not None]
                value[field] = float(np.mean(valid)) if valid else None
                value[field+"_cases"] = len(valid)
            selectors.append(value)
        snapshot.append({"target": target, "regime": regime, "block_size": size, "pools": len(pools),
            "mean_candidates": float(np.mean([p["pool_metadata"]["unique_candidates"] for p in pools])),
            "noop_fraction": float(np.mean([p["pool_metadata"]["fallback_noop"] for p in pools])),
            "illegal_proposals": sum(p["pool_metadata"]["illegal"] for p in pools), "methods": selectors})
    return {"status": "complete", "completion": completion, "groups": groups, "primary_comparisons": primary,
            "all_comparisons": comparisons, "primary_gain_rate_descriptive": rates, "shared_pool_mechanism": snapshot,
            "limits": ["13 clusters,5 seeds; one clock run/cell", "paid top2-of8 static elite donors, not actual PSO histories",
                       "FA transfer uses full stage0 and old later topology", "only strong-fast synthetic fatigue; no full optimizer/HV claim",
                       "12 main contrasts Holm corrected; all other effects and intervals exploratory"]}
