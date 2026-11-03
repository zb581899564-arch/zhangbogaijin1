"""Paired instance-level exploratory effects. Seeds are repeats, never independent instances."""
import itertools
import numpy as np


def effect(values):
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(763311)
    bootstrap = values[rng.integers(len(values), size=(5000, len(values)))].mean(axis=1)
    observed = values.mean()
    signs = np.array(list(itertools.product([-1, 1], repeat=len(values))))
    p = np.mean((signs * values).mean(axis=1) >= observed - 1e-15)
    return {"meanDelta":float(observed),"medianDelta":float(np.median(values)),
            "bootstrap95":list(map(float,np.quantile(bootstrap,[.025,.975]))),
            "wins":int((values>1e-12).sum()),"ties":int((abs(values)<=1e-12).sum()),"losses":int((values< -1e-12).sum()),
            "signFlipOneSidedP":float(p),"instanceDeltas":values.tolist()}


def holm(rows):
    adjusted = 0.
    for rank, row in enumerate(sorted(rows,key=lambda x:x["signFlipOneSidedP"])):
        adjusted = max(adjusted,min(1.,(len(rows)-rank)*row["signFlipOneSidedP"]))
        row["holmP"] = adjusted
