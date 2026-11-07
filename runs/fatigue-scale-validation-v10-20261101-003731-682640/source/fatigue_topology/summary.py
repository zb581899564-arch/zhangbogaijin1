"""Descriptive, paired summaries predeclared before the held-out run."""
from collections import defaultdict
import numpy as np
from research.fatigue_mechanism.statistics import _ranks


def average(rows, field):
    values = [row[field] for row in rows if row[field] is not None]
    return float(np.mean(values)) if values else None


def paired_interval(rows, left, right, q):
    pairs = defaultdict(dict)
    for row in rows:
        pairs[row["instance"], row["parent_seed"]][row["method"]] = row["rate_by_q"][str(q)]
    instances = sorted({key[0] for key in pairs})
    matrix = np.array([[pair[left] - pair[right] for key, pair in sorted(pairs.items()) if key[0] == name]
                       for name in instances])
    rng = np.random.default_rng(20261102)
    cluster = rng.integers(len(instances), size=(2000, len(instances), 1))
    seed = rng.integers(matrix.shape[1], size=(2000, len(instances), matrix.shape[1]))
    estimates = matrix[cluster, seed].mean(axis=(1, 2))
    return {"mean_rate_difference": float(matrix.mean()),
            "bootstrap_95_interval": np.quantile(estimates, [.025, .975]).tolist(),
            "instance_clusters": len(instances), "paired_parents": len(pairs)}


def selection_summary(selections, protocol):
    indexed = defaultdict(list)
    for row in selections:
        indexed[row["pool"], row["profile"], row["target"]].append(row)
    groups, paired = [], []
    fields = ("rank_spearman", "sign_accuracy", "accepted_gain", "selected_raw_gain",
              "improvement_probability", "oracle_regret", "tie_count")
    for (pool, profile, target), rows in indexed.items():
        for method in ("fatigue_adjoint", "time_only", "random"):
            selected = [r for r in rows if r["method"] == method]
            groups.append({"pool": pool, "profile": profile, "target": target, "method": method,
                           "parents": len(selected), **{f: average(selected, f) for f in fields},
                           "cost_ms_by_q": {str(q): float(np.mean([r["cost_ms_by_q"][str(q)] for r in selected]))
                                            for q in protocol["cache_pools_per_unchanged_parent"]},
                           "rate_by_q": {str(q): float(np.mean([r["rate_by_q"][str(q)] for r in selected]))
                                         for q in protocol["cache_pools_per_unchanged_parent"]}})
        for q in protocol["cache_pools_per_unchanged_parent"]:
            for right in ("time_only", "random"):
                paired.append({"pool": pool, "profile": profile, "target": target, "q": q,
                               "left": "fatigue_adjoint", "right": right, **paired_interval(rows, "fatigue_adjoint", right, q)})
    return groups, paired


def error_summary(observations):
    indexed = defaultdict(list)
    for row in observations:
        label = row["regime"]["full_regime" if row["pool"].startswith("probe_") else "later_regime"]
        for target, values in row["targets"].items():
            indexed[row["pool"], row["profile"], target, label].append((row, values))
    result = []
    for (pool, profile, target, label), items in indexed.items():
        actual = np.array([v["actual"] for _, v in items])
        methods = ("fatigue_adjoint", "time_only", "cut") + (("tangent",) if pool.startswith("probe_") else ())
        metrics = {}
        for method in methods:
            def score(value):
                if method == "cut":
                    return value["cut"]
                if method == "tangent":
                    return value["tangents"]["fatigue_adjoint"]
                return value["scores"][method]
            predicted = np.array([score(v) for _, v in items])
            denominator = float(np.abs(actual).sum())
            correlations = []
            by_case = defaultdict(list)
            for row, value in items:
                by_case[row["instance"], row["parent_seed"]].append((score(value), value["actual"]))
            for values in by_case.values():
                a, b = np.array(values).T
                if len(a) >= 3 and np.ptp(a) > 0 and np.ptp(b) > 0:
                    correlations.append(float(np.corrcoef(_ranks(a), _ranks(b))[0, 1]))
            metrics[method] = {"candidate_mae": float(np.mean(np.abs(predicted - actual))),
                               "wape": float(np.abs(predicted - actual).sum() / denominator) if denominator > 1e-14 else None,
                               "case_mean_spearman": float(np.mean(correlations)) if correlations else None,
                               "defined_rank_cases": len(correlations)}
        components = {name: float(np.mean([abs(v["components"][name]) for _, v in items]))
                      for name in items[0][1]["components"]}
        total = sum(components.values())
        result.append({"pool": pool, "profile": profile, "target": target, "stratum": label,
                       "candidates": len(items), "parents": len({(r["instance"], r["parent_seed"]) for r, _ in items}),
                       "mean_abs_actual": float(np.abs(actual).mean()), "methods": metrics,
                       "mean_abs_error_components": components,
                       "absolute_component_fraction": {k: v / total if total else None for k, v in components.items()},
                       "cancellation_fraction": max(0., 1 - metrics["fatigue_adjoint"]["candidate_mae"] / total) if total else None})
    return result


def summarize(observations, selections, completion, protocol):
    groups, paired = selection_summary(selections, protocol)
    counts = defaultdict(int)
    for row in observations:
        scope = "full_regime" if row["pool"].startswith("probe_") else "later_regime"
        counts[row["pool"] + ":" + row["regime"][scope]] += 1
    return {"status": "complete", "completion": completion, "regime_counts": dict(counts),
            "selection_groups": groups, "paired_rate_comparisons": paired, "error_strata": error_summary(observations),
            "limits": ["probes are not optimizer moves", "topology labels and cut scores are diagnostic only",
                       "absolute shares are ordered descriptive decomposition with cancellation",
                       "costs are Python component proxies; q>1 requires an unchanged parent",
                       "six instance clusters and many comparisons; no confirmatory superiority claim"]}
