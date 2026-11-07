"""Paired bootstrap, exact13-cluster sign flips, and one frozen12-test family."""
from collections import defaultdict
import numpy as np
from .protocol import PROTOCOL


CONTRASTS = [("cheap", "direct"), ("time", "direct"), ("fatigue", "direct"),
             ("time", "cheap"), ("fatigue", "cheap"), ("fatigue", "time"),
             ("direct", "random"), ("cheap", "random"), ("time", "random"), ("fatigue", "random")]


def paired(rows, left, right, metric="gain"):
    pairs = defaultdict(dict)
    for row in rows:
        if row["method"] in (left, right):
            pairs[row["instance"], row["parent_seed"]][row["method"]] = row[metric]
    assert all(set(v) == {left, right} for v in pairs.values())
    names = sorted({i for i, _ in pairs})
    values = np.array([[v[left]-v[right] for (i, _), v in sorted(pairs.items()) if i == name] for name in names])
    assert values.shape[1] == len(PROTOCOL["parent_seeds"])
    means, count = values.mean(axis=1), len(names)
    rng = np.random.default_rng(PROTOCOL["statistics"]["seed"])
    b = PROTOCOL["statistics"]["bootstrap"]
    cluster = rng.integers(count, size=(b, count, 1))
    seeds = rng.integers(values.shape[1], size=(b, count, values.shape[1]))
    samples = values[cluster, seeds].mean(axis=(1, 2))
    signs = ((np.arange(2**count)[:, None] >> np.arange(count)) & 1)*2-1
    p = np.mean((signs*means).mean(axis=1) >= means.mean()-1e-15)
    return {"left": left, "right": right, "metric": metric, "mean_difference": float(means.mean()),
        "bootstrap_95_interval": np.quantile(samples, [.025, .975]).tolist(),
        "exact_one_sided_p": float(p), "sign_patterns": 2**count,
        "instances": count, "paired_parents": values.size,
        "wins": int(np.sum(means > 1e-10)), "ties": int(np.sum(np.abs(means) <= 1e-10)),
        "losses": int(np.sum(means < -1e-10)), "per_instance": dict(zip(names, means.tolist()))}


def adjust_primary(rows):
    primary = PROTOCOL["primary"]
    family = [r for r in rows if r["regime"] == primary["regime"] and r["block_size"] == primary["block_size"]
              and r["target"] == primary["target"] and [r["left"], r["right"]] in primary["comparisons"]]
    assert len(family) == 12
    previous = 0.
    for i, row in enumerate(sorted(family, key=lambda r: r["exact_one_sided_p"])):
        previous = max(previous, min(1., (len(family)-i)*row["exact_one_sided_p"]))
        row["holm_adjusted_p"] = previous
        row["primary_supported"] = bool(previous < .05 and row["bootstrap_95_interval"][0] > 0)
    return family
