"""Paired instance-level inference and predeclared descriptive strata."""
from collections import defaultdict
import numpy as np
from .protocol import PROTOCOL


def differences(rows, left, right, metric):
    pairs = defaultdict(dict)
    for r in rows:
        if r["method"] in (left, right):
            pairs[r["instance"], r["parent_seed"]][r["method"]] = r[metric]
    names = sorted({i for i, _ in pairs})
    assert all(set(v) == {left, right} for v in pairs.values())
    matrix = np.array([[v[left]-v[right] for (i, _), v in sorted(pairs.items()) if i == name] for name in names])
    assert matrix.ndim == 2 and matrix.shape[1] == len(PROTOCOL["parent_seeds"])
    return names, matrix


def sign_flip(means):
    config = PROTOCOL["statistics"]
    rng, observed = np.random.default_rng(config["seed"]), float(means.mean())
    exceeded, sampled = 0, 0
    while sampled < config["sign_flip_samples"]:
        size = min(2048, config["sign_flip_samples"]-sampled)
        signs = rng.integers(0, 2, (size, len(means))) * 2-1
        values = (signs * means).mean(axis=1)
        exceeded += int(np.count_nonzero(values >= observed-1e-15))
        sampled += size
    return (exceeded+1)/(sampled+1)


def contrast(rows, left, right, metric="gain", inference=True):
    names, matrix = differences(rows, left, right, metric)
    means = matrix.mean(axis=1)
    result = {"left": left, "right": right, "metric": metric, "mean_difference": float(means.mean()),
              "median_instance_difference": float(np.median(means)), "instance_clusters": len(names),
              "paired_parents": matrix.size, "instance_wins": int(np.sum(means > 1e-10)),
              "instance_ties": int(np.sum(np.abs(means) <= 1e-10)), "instance_losses": int(np.sum(means < -1e-10)),
              "per_instance": {n: float(v) for n, v in zip(names, means)}}
    if inference:
        config = PROTOCOL["statistics"]
        rng = np.random.default_rng(config["seed"])
        cluster = rng.integers(len(names), size=(config["bootstrap_samples"], len(names), 1))
        seed = rng.integers(matrix.shape[1], size=(config["bootstrap_samples"], len(names), matrix.shape[1]))
        values = matrix[cluster, seed].mean(axis=(1, 2))
        result["bootstrap_95_interval"] = np.quantile(values, [.025, .975]).tolist()
        result["one_sided_instance_signflip_p"] = sign_flip(means)
    return result


def holm(comparisons):
    ordered = sorted(comparisons, key=lambda r: r["one_sided_instance_signflip_p"])
    previous = 0.
    for i, row in enumerate(ordered):
        previous = max(previous, min(1., (len(ordered)-i)*row["one_sided_instance_signflip_p"]))
        row["holm_adjusted_p"] = previous
        row["primary_direction_supported"] = bool(previous < .05 and row["bootstrap_95_interval"][0] > 0)


def strata(rows, original):
    groups = [(f"N={n}", [r for r in rows if int(r["instance"].split("_")[0]) == n]) for n in (20, 50, 100, 150, 200)]
    groups += [("prior6", [r for r in rows if r["instance"] in original]),
               ("new30", [r for r in rows if r["instance"] not in original])]
    result = []
    for label, selected in groups:
        for control in PROTOCOL["primary_cell"]["controls"]:
            result.append({"stratum": label, **contrast(selected, "cut_time", control, inference=False)})
    return result
