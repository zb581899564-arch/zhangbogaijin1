"""Paired instance effects, hierarchical intervals, primary12 Holm family."""
import numpy as np
from .protocol import PROTOCOL


def effects(per_parent, seed):
    # rows=independent numeric instances, columns=matched random parents.
    per_parent = np.asarray(per_parent, dtype=float)
    rng = np.random.default_rng(seed)
    b = PROTOCOL["statistics"]["bootstrap_samples"]
    n, k = per_parent.shape
    idx = rng.integers(n,size=(b,n))
    parent = rng.integers(k,size=(b,n,k))
    boot = per_parent[idx[:,:,None],parent].mean(axis=(1,2))
    means = per_parent.mean(axis=1)
    observed = means.mean()
    trials = PROTOCOL["statistics"]["sign_flip_samples"]
    flips = rng.choice((-1.,1.),size=(trials,n)) @ means/n
    p = (1+int(np.sum(flips >= observed-1e-15)))/(trials+1)
    return {"mean_difference_pp":float(observed), "CI95_pp":np.quantile(boot,[.025,.975]).tolist(),
            "sign_flip_p":p, "wins":int(np.sum(means>1e-8)), "ties":int(np.sum(np.abs(means)<=1e-8)),
            "losses":int(np.sum(means < -1e-8)), "instance_mean_differences_pp":means.tolist()}


def holm(rows):
    previous = 0.
    for rank, row in enumerate(sorted(rows,key=lambda r:r["sign_flip_p"])):
        previous = max(previous,min(1.,row["sign_flip_p"]*(len(rows)-rank)))
        row["holm_p"] = previous
