"""Offline single-candidate HV gains on frozen pools. No optimizer or evaluation calls."""
from itertools import product
import math

import numpy as np

from run_long_budget_bridge import hypervolume, igd_plus, nondominated, objectives, rows


REFS = (1.25, 1.5, 2.0)
EPS = 1e-12


def compare(trials, norm):
    lower, scale = np.asarray(norm["lower"]), np.asarray(norm["scale"])
    fronts = {label: {r["fe"]: (np.asarray(r["front"]) - lower) / scale for r in run["curve"]}
              for label, run in trials.items()}
    end = max(fronts["SPECIAL"])
    reference = nondominated(np.concatenate([front[end] for front in fronts.values()]))
    result = []
    for fe in fronts["SPECIAL"]:
        arms = {}
        for label, front in fronts.items():
            f = front[fe]
            arms[label] = {"HV": {str(r): float(hypervolume(f, (r,) * 3)) for r in REFS},
                           "IGDplus": float(igd_plus(f, reference)), "size": len(f),
                           "objectiveMinima": (f.min(axis=0) * scale + lower).tolist(),
                           "outsideMainBox": int(np.sum(np.any(f >= 1.5, axis=1)))}
        s, u, n = [arms[label]["HV"] for label in ("SPECIAL", "UNIFORM", "NSGA")]
        result.append({"FE": fe, "arms": arms, "specialVsUniform": {r: s[r] / u[r] - 1 for r in s},
                       "specialVsNsga": {r: s[r] / n[r] - 1 for r in s}})
    return result


def single_gains(front, candidates):
    """Integrate the part of each candidate box uncovered by the current 3D archive."""
    if not len(candidates):
        return np.empty(0)
    front = nondominated(front[np.all(front < 1.5, axis=1)])
    candidates = np.asarray(candidates)
    gains = np.zeros(len(candidates))
    x_edges = np.unique(np.r_[front[:, 0], min(1.5, candidates[:, 0].min()), 1.5])
    y_min = min(1.5, candidates[:, 1].min())
    for x0, x1 in zip(x_edges, x_edges[1:]):
        active = front[front[:, 0] <= x0]
        active = active[np.argsort(active[:, 1], kind="stable")]
        width = np.maximum(x1 - np.maximum(x0, candidates[:, 0]), 0)
        area, y0, z = np.zeros(len(candidates)), y_min, 1.5
        for _, y1, cap in active:
            if cap >= z:
                continue
            if y1 > y0:
                area += np.maximum(y1 - np.maximum(y0, candidates[:, 1]), 0) * np.maximum(z - candidates[:, 2], 0)
                y0 = y1
            z = cap
        area += np.maximum(1.5 - np.maximum(y0, candidates[:, 1]), 0) * np.maximum(z - candidates[:, 2], 0)
        gains += width * area
    # Spot-check the integration against the existing independent archive-HV implementation.
    hv = hypervolume(front, (1.5,) * 3)
    for i in {0, len(candidates) - 1, int(np.argmax(gains))}:
        direct = hypervolume(np.vstack((front, candidates[i])), (1.5,) * 3) - hv
        assert math.isclose(direct, gains[i], abs_tol=EPS, rel_tol=0), (direct, gains[i])
    return gains


def genome(record):
    return tuple(tuple(record[k]) for k in ("jobs", "machines", "workers"))


def aggregate(records):
    a = [r["objectives"] for r in records]
    return (max(x[0] for x in a), sum(x[1] for x in a), sum(x[2] for x in a))


def same_job_sets(source, receiver):
    return (len(source["factories"]) == len(receiver["factories"]) == 3
            and all(f["factory"] == g["factory"] and set(f["parent"]["jobs"]) == set(g["parent"]["jobs"])
                    for f, g in zip(source["factories"], receiver["factories"])))


def check_snapshot(snapshot, admitted):
    paid = snapshot["paidFE"]
    assert objectives(snapshot["archive"]) == objectives(nondominated([p for t, p in admitted if t <= paid]))
    assert len(snapshot["factories"]) == 3
    for factory in snapshot["factories"]:
        assert len(factory["records"]) <= 8
        parent = set(factory["parent"]["jobs"])
        assert all(set(r["jobs"]) == parent and len(r["jobs"]) == len(parent)
                   and 0 < r["paidFE"] <= paid for r in factory["records"])


def best_witness(gains, combos, vectors, mask):
    indices = np.flatnonzero(mask)
    if not len(indices):
        return {"gain": 0.0, "objectives": None}
    i = int(indices[np.argmax(gains[indices])])
    return {"gain": float(gains[i]), "objectives": vectors[i],
            "sourcePaidFE": [r["paidFE"] for r in combos[i]],
            "sourceStages": [r["stage"] for r in combos[i]], "sourceRoles": [r["producer"] for r in combos[i]]}


def pool_gain(source, receiver, front, norm, verify_actual=False):
    assert same_job_sets(source, receiver)
    lower, scale = np.asarray(norm["lower"]), np.asarray(norm["scale"])
    a = (np.asarray(front) - lower) / scale
    pools = [f["records"] for f in source["factories"]]
    parent = [genome(f["parent"]) for f in receiver["factories"]]
    cap, eta = receiver["cap"], receiver["eta"]
    feasible = [[r for r in pool if r["objectives"][0] <= cap] for pool in pools]
    chosen = [min(pool, key=lambda r: r["objectives"][1] / receiver["energyScale"]
                  + eta * r["objectives"][2] / receiver["wageScale"]) if pool else None for pool in feasible]
    if any(r is None for r in chosen):
        outcome = "INFEASIBLE"
    elif [genome(r) for r in chosen] == parent:
        outcome = "DUPLICATE_PARENT"
    else:
        outcome = "PROPOSED"
    if verify_actual:
        assert outcome == receiver["outcome"]
        assert chosen == [f["chosen"] for f in receiver["factories"]]
    combos = [r for r in product(*pools) if [genome(x) for x in r] != parent]
    assert len(combos) <= 512
    vectors = [aggregate(r) for r in combos]
    gains = single_gains(a, (np.asarray(vectors) - lower) / scale if vectors else [])
    cap_mask = np.asarray([v[0] <= cap for v in vectors], dtype=bool)
    actual = 0.0
    if outcome == "PROPOSED":
        idx, = [i for i, combo in enumerate(combos) if tuple(chosen) == combo]
        actual = float(gains[idx])
    return {"archiveHV": float(hypervolume(a, (1.5,) * 3)), "combos": len(combos),
            "combosInCap": int(cap_mask.sum()), "ruleOutcome": outcome, "ruleGain": actual,
            "uniformExpected": float(gains.mean()) if len(gains) else 0.0,
            "uniformExpectedInCap": float(gains[cap_mask].mean()) if cap_mask.any() else 0.0,
            "bestInCap": best_witness(gains, combos, vectors, cap_mask),
            "bestCompatible": best_witness(gains, combos, vectors, np.ones(len(combos), dtype=bool))}


def pool_diagnosis(trial_folders, norm):
    import csv
    samples, own, expected = {}, {}, {}
    for label, folder in trial_folders.items():
        snapshots = rows(folder / "pool-snapshots.jsonl")
        window, = rows(folder / "pool-window.jsonl")
        expected[label] = 8 * len({g for g in (window["first"], window["last"]) if g is not None})
        with (folder / "archive-admissions.csv").open(encoding="utf-8", newline="") as f:
            admitted = [(int(r["fe"]), [float(r[k]) for k in ("cmax", "tec", "twc")]) for r in csv.DictReader(f)]
        samples[label], own[label] = {}, []
        for s in snapshots:
            check_snapshot(s, admitted)
            key = (s["generation"], s["family"], s["paidFE"])
            assert key not in samples[label]
            samples[label][key] = s
            result = pool_gain(s, s, s["archive"], norm, verify_actual=True)
            best, actual, base = result["bestCompatible"]["gain"], result["ruleGain"], result["archiveHV"]
            result["missed"] = base > 0 and best >= 0.001 * base and actual < 0.5 * best
            own[label].append({"key": key, "request": s["request"], **result})
        assert len(snapshots) <= expected[label] <= 16
    special, uniform = samples["SPECIAL"], samples["UNIFORM"]
    cross, missing = [], []
    for key in sorted(set(special) | set(uniform)):
        if key not in special or key not in uniform:
            missing.append({"key": key, "reason": "missing matched request"}); continue
        s, u = special[key], uniform[key]
        if not same_job_sets(s, u):
            missing.append({"key": key, "reason": "incompatible factory jobs"}); continue
        front = nondominated(s["archive"] + u["archive"]).tolist()
        row = {"key": key, "receivers": {}}
        for label, recipient in (("SPECIAL", s), ("UNIFORM", u)):
            sr, ur = pool_gain(s, recipient, front, norm), pool_gain(u, recipient, front, norm)
            delta = sr["bestCompatible"]["gain"] - ur["bestCompatible"]["gain"]
            row["receivers"][label] = {"specialPool": sr, "uniformPool": ur, "difference": delta,
                                       "materialWin": delta > EPS and delta >= 0.001 * sr["archiveHV"]}
        cross.append(row)
    stats = {}
    for label in samples:
        subset = [row["receivers"][label] for row in cross]
        stats[label] = {"wins": sum(r["difference"] > EPS for r in subset),
                        "losses": sum(r["difference"] < -EPS for r in subset),
                        "materialWins": sum(r["materialWin"] for r in subset)}
    families = sorted({r["key"][1] for r in cross})
    supply = len(cross) >= 8 and len(families) >= 2 and all(
        r["wins"] > r["losses"] and r["materialWins"] / len(cross) >= 0.2 for r in stats.values())
    omissions = [r for r in own["SPECIAL"] if r["missed"]]
    omitted_families = sorted({r["key"][1] for r in omissions})
    fraction = len(omissions) / expected["SPECIAL"] if expected["SPECIAL"] else 0
    return {"searchFE": 0, "expectedSampleSlots": expected, "observedSampleCounts": {k: len(v) for k, v in own.items()},
            "own": own, "cross": cross, "missingCross": missing, "matchedPairs": len(cross),
            "matchedFamilies": families, "supplyStats": stats, "supplyGate": supply,
            "materialOmissions": len(omissions), "omissionFamilies": omitted_families,
            "omissionFraction": fraction, "omissionGate": len(omitted_families) >= 2 and fraction >= 0.2}
