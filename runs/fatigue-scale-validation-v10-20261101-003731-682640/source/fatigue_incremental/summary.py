"""Average clock repeats within parent before paired instance/seed inference."""
from collections import Counter, defaultdict
import numpy as np
from research.fatigue_reuse.summary import reuse_statistics


MEAN_FIELDS = ("gain", "elapsed_ns", "overrun_ns", "attempted_decisions", "on_time_decisions", "accepted")


def collapse_repeats(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["instance"], row["parent_seed"], row["method"]].append(row)
    result = []
    for (instance, seed, method), runs in grouped.items():
        value = {"instance": instance, "parent_seed": seed, "method": method, "repeats": len(runs)}
        value.update({field: float(np.mean([r[field] for r in runs])) for field in MEAN_FIELDS})
        value["gain_per_second"] = float(np.mean([r["gain"] / (r["elapsed_ns"] / 1e9) for r in runs]))
        result.append(value)
    return result


def paired(rows, left, right, metric):
    pairs = defaultdict(dict)
    for row in rows:
        if row["method"] in (left, right):
            pairs[row["instance"], row["parent_seed"]][row["method"]] = row[metric]
    names = sorted({k[0] for k in pairs})
    matrix = np.array([[v[left]-v[right] for k, v in sorted(pairs.items()) if k[0] == name] for name in names])
    rng = np.random.default_rng(20261109)
    cluster = rng.integers(len(names), size=(2000, len(names), 1))
    seed = rng.integers(matrix.shape[1], size=(2000, len(names), matrix.shape[1]))
    samples = matrix[cluster, seed].mean(axis=(1, 2))
    return {"mean_difference": float(matrix.mean()), "bootstrap_95_interval": np.quantile(samples, [.025, .975]).tolist(),
            "instance_clusters": len(names), "paired_parents": len(pairs)}


def work_summary(rows):
    total = Counter()
    for row in rows:
        total.update(row["incremental_work"])
    equivalent = total["equivalent_full_ops"]
    return {"counts": dict(total), "recomputed_fraction": total["recomputed_ops"] / equivalent if equivalent else None,
            "prefix_reused_fraction": total["reused_prefix_ops"] / equivalent if equivalent else None,
            "unaffected_factory_fraction": total["unchanged_factory_ops"] / equivalent if equivalent else None}


def summarize(chains, epochs, calibration, ablations, completion):
    grouped, epoch_groups = defaultdict(list), defaultdict(list)
    for row in chains:
        grouped[row["mode"], row["profile"], row["target"]].append(row)
    for epoch in epochs:
        epoch_groups[epoch["mode"], epoch["profile"], epoch["target"], epoch["method"]].append(epoch)
    groups, comparisons, kernel_comparisons, repeats = [], [], [], []
    for (mode, profile, target), rows in grouped.items():
        parents = collapse_repeats(rows)
        for method in dict.fromkeys(r["method"] for r in rows):
            raw = [r for r in rows if r["method"] == method]
            selected = [r for r in parents if r["method"] == method]
            wall = sum(r["elapsed_ns"] for r in raw)
            groups.append({"mode": mode, "profile": profile, "target": target, "method": method,
               "runs": len(raw), "paired_parents": len(selected),
               **{f: float(np.mean([r[f] for r in selected])) for f in MEAN_FIELDS},
               "gain_per_second": float(np.mean([r["gain_per_second"] for r in selected])),
               "stage0_time_fraction": sum(r["stage0_ns"] for r in raw)/wall,
               "cache_time_fraction": sum(r["phases_ns"].get("cache_build", 0) for r in raw)/wall,
               "reuse": reuse_statistics(epoch_groups[mode, profile, target, method]),
               "work": work_summary(raw)})
        for right in ("cut_time", "local_time", "random"):
            for metric in ("gain", "gain_per_second"):
                comparisons.append({"mode": mode, "profile": profile, "target": target, "metric": metric,
                                    "left": "cut_fatigue", "right": right, **paired(parents, "cut_fatigue", right, metric)})
        if any(r["method"].endswith("_full") for r in rows):
            repeat0 = collapse_repeats([r for r in rows if r["repeat"] == 0])
            for left in ("cut_fatigue", "cut_time"):
                kernel_comparisons.append({"mode": mode, "profile": profile, "target": target,
                   "left": left, "right": left + "_full", "repeat": 0,
                   **paired(repeat0, left, left + "_full", "gain")})
        if mode == "time" and profile == "strong_fast_recovery" and target == "TEC":
            for repeat in (0, 1, 2):
                subset = collapse_repeats([r for r in rows if r["repeat"] == repeat])
                for right in ("cut_time", "local_time", "random"):
                    repeats.append({"repeat": repeat, "left": "cut_fatigue", "right": right,
                                    **paired(subset, "cut_fatigue", right, "gain")})
    components = {name: {"mean_ms": float(np.mean([r["component_timings"][name]["median_ms"] for r in calibration]))}
                  for name in calibration[0]["component_timings"]}
    implementation = []
    for selector in ("cut_fatigue", "cut_time"):
        rows = [r for r in ablations if r["selector"] == selector]
        implementation.append({"selector": selector, "pairs": len(rows), "all_trajectories_identical": all(r["same_scores_and_trajectory"] for r in rows),
           "median_full_over_incremental_time": float(np.median([r["full_elapsed_ns"]/r["incremental_elapsed_ns"] for r in rows])),
           "mean_elapsed_saved_ms": float(np.mean([(r["full_elapsed_ns"]-r["incremental_elapsed_ns"])/1e6 for r in rows])),
           "median_full_over_incremental_stage0": float(np.median([r["full_stage0_ns"]/r["incremental_stage0_ns"] for r in rows]))})
    return {"status": "complete", "completion": completion, "groups": groups, "paired_comparisons": comparisons,
            "repeat_comparisons": repeats, "same_repeat_kernel_comparisons": kernel_comparisons,
            "component_calibration": components, "implementation_ablation": implementation,
            "limits": ["clock repeats averaged per parent, not independent cases", "six instance clusters; descriptive bootstrap",
                       "scalar local chains, no multiobjective optimizer/HV claims", "all online overhead counted, offline QA and disk output separate"]}
