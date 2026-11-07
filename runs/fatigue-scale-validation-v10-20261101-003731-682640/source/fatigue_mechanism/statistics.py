"""Paired mechanism metrics; uniform ties and hierarchical instance-level resampling."""
from __future__ import annotations

import numpy as np


def _ranks(values):
    values = np.asarray(values)
    order = np.argsort(values, kind="stable")
    ranks = np.empty(len(values), dtype=float)
    start = 0
    while start < len(order):
        stop = start + 1
        while stop < len(order) and values[order[stop]] == values[order[start]]:
            stop += 1
        ranks[order[start:stop]] = (start + stop - 1) / 2
        start = stop
    return ranks


def select_minima(scores):
    """Uniform tie support, determined before looking at any candidate truth."""
    scores = np.asarray(scores)
    tolerance = 1e-12 * max(1.0, float(np.max(np.abs(scores))))
    return np.flatnonzero(scores <= np.min(scores) + tolerance)


def selection_metrics(scores, actual_delta):
    actual = np.asarray(actual_delta)
    if scores is None:
        chosen = np.arange(len(actual))
        correlation = None
        sign_accuracy = None
    else:
        scores = np.asarray(scores)
        chosen = select_minima(scores)
        a, b = _ranks(scores), _ranks(actual)
        correlation = float(np.corrcoef(a, b)[0, 1]) if np.ptp(a) > 0 and np.ptp(b) > 0 else None
        sign_accuracy = float(np.mean((scores < -1e-10) == (actual < -1e-10)))
    gain = -actual[chosen]
    return {"tie_indices":chosen.tolist(),"tie_count":len(chosen),"rank_spearman":correlation,
            "sign_accuracy":sign_accuracy,"improvement_probability":float(np.mean(gain > 1e-10)),
            "selected_raw_gain":float(np.mean(gain)),"accepted_gain":float(np.mean(np.maximum(0.0, gain))),
            "oracle_regret":float(np.mean(actual[chosen]) - np.min(actual))}


def paired_bootstrap(rows, left, right, metric="accepted_gain", repeats=2000, seed=20261101):
    pairs = {}
    for row in rows:
        key = (row["instance"], row["parent_seed"], row["profile"], row["target"])
        pairs.setdefault(key, {})[row["method"]] = row[metric]
    data = [(key[0], value[left] - value[right]) for key, value in pairs.items()]
    groups = {name:np.asarray([delta for group, delta in data if group == name]) for name in sorted({x[0] for x in data})}
    rng = np.random.default_rng(seed)
    names = list(groups)
    estimates = []
    for _ in range(repeats):
        values = []
        for index in rng.integers(len(names), size=len(names)):
            group = groups[names[index]]
            values.extend(rng.choice(group, size=len(group), replace=True))
        estimates.append(np.mean(values))
    return {"mean_difference":float(np.mean([delta for _, delta in data])),
            "bootstrap_95_interval":list(map(float, np.quantile(estimates, [0.025, 0.975]))),
            "clusters":len(groups),"paired_units":len(pairs),
            "scope":"descriptive diagnostic interval; six reconstructed instances are not population proof"}
