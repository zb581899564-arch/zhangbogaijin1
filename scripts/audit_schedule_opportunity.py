"""Goal gate 1: locate archive gaps and legal encoding differences without new search FE."""
from datetime import datetime
from collections import Counter
from pathlib import Path
import shutil

import numpy as np

from run_long_budget_bridge import ROOT, hypervolume, nondominated, objectives, read, rows, write_once


SOURCE = ROOT / "runs/pddr-role-budget-20261104-095957/DEEP"
PRIOR = ROOT / "runs/dynamic-reverse-ledger-20261103-231754-095093"


def by_job(row, names=("FA", "MA", "WA")):
    n = len(row["JS"])
    result = np.empty((n, len(names)), dtype=int)
    for pos, job in enumerate(row["JS"]):
        for j, name in enumerate(names):
            result[job, j] = row[name][pos]
    return result


def order_distance(a, b):
    pa, pb = np.argsort(a["JS"]), np.argsort(b["JS"])
    inversions = sum((pa[i] < pa[j]) != (pb[i] < pb[j])
                     for i in range(len(pa)) for j in range(i + 1, len(pa)))
    return inversions / (len(pa) * (len(pa) - 1) / 2)


def summarize_pair(s, n, i, j):
    a, b = by_job(s), by_job(n)
    same_factory = a[:, 0] == b[:, 0]
    return {"specialIndex": i, "nsgaIndex": j, "specialObjectives": s["objectives"], "nsgaObjectives": n["objectives"],
            "FAJobChanges": int(np.sum(~same_factory)),
            "MAChangesInUnmovedJobs": int(np.sum(same_factory & (a[:, 1] != b[:, 1]))),
            "WAChangesInUnmovedJobs": int(np.sum(same_factory & (a[:, 2] != b[:, 2]))),
            "orderKendall": order_distance(s, n)}


def analyze(root):
    solutions = {a: rows(SOURCE / f"{a}-LINEAR/solutions.jsonl") for a in ("SPECIAL", "NSGA")}
    vectors = {a: np.asarray([r["objectives"] for r in v]) for a, v in solutions.items()}
    norm = read(PRIOR / "protocol.json")["normalization"]
    f = {a: (v - norm["lower"]) / norm["scale"] for a, v in vectors.items()}
    s, n = f["SPECIAL"], f["NSGA"]
    n_weak_s = np.all(n[:, None] <= s[None, :], axis=2)
    s_weak_n = np.all(s[:, None] <= n[None, :], axis=2)
    outside_s = np.flatnonzero(~np.any(s_weak_n, axis=0))
    outside_n = np.flatnonzero(~np.any(n_weak_s, axis=0))
    joint = np.concatenate((s, n))
    edges = np.unique(np.r_[0, np.quantile(joint[:, 0], [.0, .25, .5, .75, 1]), 1.5])
    slabs = []
    for a, b in zip(edges, edges[1:]):
        part = {}
        for label, points in f.items():
            q = points.copy()
            q[:, 0] = np.maximum(a, q[:, 0])
            part[label] = float(hypervolume(q, (b, 1.5, 1.5)))
        slabs.append({"CmaxFrom": a * norm["scale"][0], "CmaxTo": b * norm["scale"][0],
                      "HV": part, "nsgaMinusSpecial": part["NSGA"] - part["SPECIAL"]})
    for label in f:
        assert abs(sum(r["HV"][label] for r in slabs) - hypervolume(f[label], (1.5,) * 3)) < 1e-12
    genes = {a: np.asarray([by_job(row) for row in v]) for a, v in solutions.items()}
    signatures = {a: {tuple(x[:, 0]) for x in g} for a, g in genes.items()}
    families = [tuple(by_job(r)[:, 0]) for r in rows(PRIOR / "SPECIAL/trials/fatigue/SHARE_JOB_ALIGNED/initial-population.jsonl")[:20:5]]
    pairs = []
    for j in outside_s:
        delta = s - n[j]
        distance = np.sqrt(np.sum(delta * delta, axis=1))
        i = int(np.argmin(distance))
        pairs.append(summarize_pair(solutions["SPECIAL"][i], solutions["NSGA"][j], i, int(j)))
    equal_fa = []
    for j in outside_s:
        match = np.flatnonzero(np.all(genes["SPECIAL"][:, :, 0] == genes["NSGA"][j, :, 0], axis=1))
        if len(match):
            distances = np.linalg.norm(s[match] - n[j], axis=1)
            equal_fa.append(summarize_pair(solutions["SPECIAL"][int(match[np.argmin(distances)])],
                                         solutions["NSGA"][j], int(match[np.argmin(distances)]), int(j)))
    report = {"source": str(SOURCE), "searchFE": 0, "sizes": {a: len(v) for a, v in solutions.items()},
              "minima": {a: v.min(axis=0).tolist() for a, v in vectors.items()},
              "hv": {a: float(hypervolume(points, (1.5,) * 3)) for a, points in f.items()},
              "coverage": {"nsgaWeaklyCoversSpecial": float(np.any(n_weak_s, axis=0).mean()),
                           "specialWeaklyCoversNsga": float(np.any(s_weak_n, axis=0).mean())},
              "notCovered": {"nsga": len(outside_s), "special": len(outside_n)},
              "FA": {a: {"unique": len(signatures[a]), "inFixedFamily": sum(tuple(g[:, 0]) in families for g in genes[a])}
                     for a in genes},
              "sharedFASignatures": len(signatures["SPECIAL"] & signatures["NSGA"]),
              "nsgaNotCoveredButSameFAExists": len(equal_fa),
              "CmaxSlabs": slabs, "nearestPairs": pairs, "sameFAPairs": equal_fa}
    for name, data in solutions.items():
        write_once(root / f"source-{name}.json", data)
    write_once(root / "opportunity.json", report)
    return report


def main():
    root = ROOT / "runs" / datetime.now().strftime("three-gates-opportunity-%Y%m%d-%H%M%S-%f")
    root.mkdir()
    shutil.copy2(Path(__file__), root)
    write_once(root / "protocol.json", {
        "phase": "gate1 existing-evidence audit", "sources": str(SOURCE), "searchFE": 0,
        "regions": "Cmax slabs at pooled terminal quartiles; additive HV difference, descriptive only",
        "pairs": "All NSGA targets not weakly covered by SPECIAL; nearest normalized objective neighbor, "
                 "plus exact per-job FA matched subsets. Structural correlation is not causal attribution."})
    report = analyze(root)
    write_once(root / "status.json", {"status": "COMPLETE", "searchFE": 0})
    print("OPPORTUNITY_ROOT", root, flush=True)
    print({k: report[k] for k in ("hv", "minima", "coverage", "notCovered", "FA", "sharedFASignatures",
                                 "nsgaNotCoveredButSameFAExists", "CmaxSlabs")}, flush=True)


if __name__ == "__main__":
    main()
