"""Whole-cell and work/cost summaries, keeping scalar objectives explicit."""
from collections import Counter, defaultdict
import numpy as np
from research.fatigue_incremental.protocol import PROTOCOL as V4
from .protocol import PROTOCOL
from .statistics import contrast, holm, strata


def method_summary(rows):
    total = sum(r["elapsed_ns"] for r in rows)
    work = Counter()
    for r in rows:
        work.update(r["incremental_work"])
    equivalent = work["equivalent_full_ops"]
    fractions = {f: work[f]/equivalent if equivalent else None for f in ("recomputed_ops", "reused_prefix_ops", "unchanged_factory_ops")}
    return {"method": rows[0]["method"], "runs": len(rows), "instance_clusters": len({r['instance'] for r in rows}),
        "mean_gain": float(np.mean([r["gain"] for r in rows])),
        "mean_gain_per_second": float(np.mean([r["gain_per_second"] for r in rows])),
        "mean_elapsed_ms": float(np.mean([r["elapsed_ns"] for r in rows]))/1e6,
        "mean_overrun_ms": float(np.mean([r["overrun_ns"] for r in rows]))/1e6,
        "mean_on_time_decisions": float(np.mean([r["on_time_decisions"] for r in rows])),
        "mean_accepted": float(np.mean([r["accepted"] for r in rows])),
        "mean_objective_gains": np.mean([1-np.asarray(r["final_objectives"])/r["initial_objectives"] for r in rows], axis=0).tolist(),
        "stage0_time_fraction": sum(r["stage0_ns"] for r in rows)/total,
        "cache_time_fraction": sum(r["phases_ns"].get("cache_build", 0) for r in rows)/total,
        "work": dict(work), "work_fractions": fractions}


def summarize(chains, ablations, completion):
    cells = defaultdict(list)
    for row in chains:
        row["gain_per_second"] = row["gain"]/(row["elapsed_ns"]/1e9)
        if row["mode"] == "time":
            cells[row["profile"], row["target"], row["budget_seconds"]].append(row)
    groups, primary, secondary, rates, stratified = [], [], [], [], []
    for (profile, target, budget), rows in sorted(cells.items()):
        cell = {"profile": profile, "target": target, "budget_seconds": budget}
        groups.append({**cell, "methods": [method_summary([r for r in rows if r["method"] == m]) for m in PROTOCOL["methods"]]})
        main = profile == "strong_fast_recovery" and target == "TEC"
        for control in PROTOCOL["primary_cell"]["controls"]:
            comparison = {**cell, **contrast(rows, "cut_time", control)}
            (primary if main else secondary).append(comparison)
            if main:
                rates.append({**cell, **contrast(rows, "cut_time", control, "gain_per_second")})
        if main:
            stratified.extend({**cell, **r} for r in strata(rows, V4["instances"]))
    assert len(primary) == 8
    holm(primary)
    implementation = {"pairs": len(ablations), "all_scores_and_trajectories_identical": all(r["same_scores_and_trajectory"] for r in ablations),
        "median_full_over_incremental_time": float(np.median([r["full_elapsed_ns"]/r["incremental_elapsed_ns"] for r in ablations])),
        "mean_elapsed_saved_ms": float(np.mean([(r["full_elapsed_ns"]-r["incremental_elapsed_ns"])/1e6 for r in ablations])),
        "median_full_over_incremental_stage0": float(np.median([r["full_stage0_ns"]/r["incremental_stage0_ns"] for r in ablations]))}
    return {"status": "complete", "completion": completion, "groups": groups,
            "primary_comparisons": primary, "primary_rate_comparisons_descriptive": rates,
            "secondary_comparisons_exploratory": secondary, "predeclared_strata_descriptive": stratified,
            "implementation_ablation": implementation,
            "limits": ["synthetic fatigue and reconstructed SUT/standby", "36 instance clusters and only3 seeds each",
                       "one clock run per method/case/budget", "no full optimizer/HV/IGD+ or novelty claim",
                       "primary8 Holm corrected, bootstrap intervals and secondary/strata unadjusted"]}
