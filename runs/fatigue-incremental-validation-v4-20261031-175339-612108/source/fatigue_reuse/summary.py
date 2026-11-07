"""Paired instance/seed summaries of measured chains, not amortized proxies."""
from collections import defaultdict
import numpy as np


def gain_rate(row):
    return row["gain"] / (row["elapsed_ns"] / 1e9)


def paired(rows, right, metric):
    pairs = defaultdict(dict)
    for row in rows:
        pairs[row["instance"], row["parent_seed"]][row["method"]] = row
    names = sorted({key[0] for key in pairs})
    value = gain_rate if metric == "gain_per_second" else lambda r: r[metric]
    matrix = np.array([[value(pair["cut_fatigue"]) - value(pair[right])
                        for key, pair in sorted(pairs.items()) if key[0] == name] for name in names])
    rng = np.random.default_rng(20261105)
    cluster = rng.integers(len(names), size=(2000, len(names), 1))
    seed = rng.integers(matrix.shape[1], size=(2000, len(names), matrix.shape[1]))
    means = matrix[cluster, seed].mean(axis=(1, 2))
    return {"mean_difference": float(matrix.mean()), "bootstrap_95_interval": np.quantile(means, [.025, .975]).tolist(),
            "clusters": len(names), "paired_parents": len(pairs)}


def reuse_statistics(epochs):
    if not epochs:
        return None
    uses = np.array([e["uses"] for e in epochs])
    closed = [e["uses"] for e in epochs if e["closed_reason"] == "accepted"]
    terminal = [e["uses"] for e in epochs if e["closed_reason"] == "terminal_right_censored"]
    return {"cache_epochs": len(epochs), "mean_q": float(uses.mean()), "median_q": float(np.median(uses)),
            "p90_q": float(np.quantile(uses, .9)), "fraction_q_ge4": float(np.mean(uses >= 4)),
            "accepted_epochs": len(closed), "accepted_epoch_mean_q": float(np.mean(closed)) if closed else None,
            "accepted_epoch_fraction_q_ge4": float(np.mean(np.asarray(closed) >= 4)) if closed else None,
            "terminal_censored_epochs": len(terminal), "terminal_mean_q": float(np.mean(terminal)) if terminal else None,
            "on_time_uses": sum(e["on_time_uses"] for e in epochs)}


def summarize(chains, epochs, calibration, ablations, completion):
    grouped, epoch_groups = defaultdict(list), defaultdict(list)
    for row in chains:
        if row["method"] != "cut_fatigue_fresh":
            grouped[row["mode"], row["profile"], row["target"]].append(row)
    for epoch in epochs:
        epoch_groups[epoch["mode"], epoch["profile"], epoch["target"], epoch["method"]].append(epoch)
    groups, comparisons = [], []
    for (mode, profile, target), rows in grouped.items():
        for method in ("cut_fatigue", "cut_time", "local_time", "random"):
            selected = [r for r in rows if r["method"] == method]
            wall = sum(r["elapsed_ns"] for r in selected)
            groups.append({"mode": mode, "profile": profile, "target": target, "method": method,
                 "chains": len(selected), "gain": float(np.mean([r["gain"] for r in selected])),
                 "gain_per_second": float(np.mean([gain_rate(r) for r in selected])),
                 "elapsed_ms": float(np.mean([r["elapsed_ns"] / 1e6 for r in selected])),
                 "overrun_ms": float(np.mean([r["overrun_ns"] / 1e6 for r in selected])),
                 "attempted_decisions": float(np.mean([r["attempted_decisions"] for r in selected])),
                 "on_time_decisions": float(np.mean([r["on_time_decisions"] for r in selected])),
                 "accepted": float(np.mean([r["accepted"] for r in selected])),
                 "stage0_time_fraction": sum(r["stage0_ns"] for r in selected) / wall,
                 "phase_time_fraction": {p: sum(r["phases_ns"].get(p, 0) for r in selected) / wall
                                         for p in ("initial_decode", "generation", "cache_build", "scoring", "selection", "child_decode")},
                 "reuse": reuse_statistics(epoch_groups[mode, profile, target, method])})
        for right in ("cut_time", "local_time", "random"):
            for metric in ("gain", "gain_per_second"):
                comparisons.append({"mode": mode, "profile": profile, "target": target,
                                    "left": "cut_fatigue", "right": right, "metric": metric, **paired(rows, right, metric)})
    component = {}
    for name in calibration[0]["component_timings"]:
        values = [r["component_timings"][name]["median_ms"] for r in calibration]
        component[name] = {"mean_ms": float(np.mean(values)), "median_ms": float(np.median(values))}
    ablation = {"pairs": len(ablations), "all_trajectories_identical": all(r["same_complete_trajectory"] for r in ablations),
                "mean_cached_q": float(np.mean([r["cached_q"] for r in ablations])),
                "mean_builds_saved": float(np.mean([r["fresh_builds"] - r["cached_builds"] for r in ablations])),
                "median_fresh_over_cached_time": float(np.median([r["fresh_elapsed_ns"] / r["cached_elapsed_ns"] for r in ablations])),
                "mean_elapsed_saved_ms": float(np.mean([(r["fresh_elapsed_ns"] - r["cached_elapsed_ns"]) / 1e6 for r in ablations]))}
    return {"status": "complete", "completion": completion, "groups": groups, "paired_comparisons": comparisons,
            "calibration": component, "reuse_ablation": ablation,
            "limits": ["standalone scalar local chains only, no full optimizer/HV conclusion", "synthetic fatigue and reconstructed SUT/standby",
                       "JSON I/O, common data load and offline QA excluded from search clock and separately accounted",
                       "non-preemptive overrun reported; deadline gain excludes late child improvements",
                       "six instance clusters, descriptive paired bootstrap", "trajectories diverge after acceptance; identical rules do not imply identical future pools"]}
